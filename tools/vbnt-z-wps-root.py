#!/usr/bin/env python3
"""Build and import a password-signed VBNT-Z config with a one-shot WPS root-shell fix."""

import argparse
import binascii
import getpass
import hashlib
import hmac
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

import vbnt_z_mysrp as srp


WPS_HANDLER = (
    'button.wps.handler=\'sed -i "s#/bin/restricted_shell#/bin/ash#" '
    "/etc/passwd; /etc/init.d/dropbear restart\'"
)


def parse_header(blob):
    end = blob.find(b"\n\n")
    if end < 0:
        raise ValueError("not a THENC configuration")
    header = blob[: end + 2]
    fields = {}
    for line in blob[:end].decode("ascii", "replace").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            fields[key] = value
    if fields.get("PREAMBLE") != "THENC" or fields.get("BOARDMNEMONIC") != "VBNT-Z":
        raise ValueError("configuration is not for a VBNT-Z")
    return end, header, fields


def config_key(password):
    digest = hashlib.sha1(("VBNT-Z" + password).encode()).hexdigest()
    return digest.encode()[:32]


def modify_plaintext(text):
    replacements = {
        "dropbear.lan.RootPasswordAuth='off'": "dropbear.lan.RootPasswordAuth='on'",
        "dropbear.lan.enable='0'": "dropbear.lan.enable='1'",
        "dropbear.lan.RootLogin='0'": "dropbear.lan.RootLogin='1'",
        "dropbear.lan.PasswordAuth='off'": "dropbear.lan.PasswordAuth='on'",
        "button.wps.handler='wps_button_pressed.sh'": WPS_HANDLER,
    }
    for old, new in replacements.items():
        if old not in text and new not in text:
            raise ValueError(f"expected configuration line missing: {old}")
        text = text.replace(old, new)
    if "system.config.import_restricted=" not in text:
        marker = "system.config.import_unsigned='0'"
        if marker not in text:
            raise ValueError("system.config section not found")
        text = text.replace(marker, marker + "\nsystem.config.import_restricted='0'")
    return text


def build_config(source, output, password):
    blob = source.read_bytes()
    end, header, _ = parse_header(blob)
    body = blob[end + 2 :]
    if len(body) < 36:
        raise ValueError("configuration body is too short")
    key = config_key(password)
    if not hmac.compare_digest(hmac.new(key, blob[:-20], hashlib.sha1).digest(), body[-20:]):
        raise ValueError("backup signature or password is invalid")
    plaintext = unpad(AES.new(key, AES.MODE_CBC, body[:16]).decrypt(body[16:-20]), 16)
    modified = modify_plaintext(plaintext.decode("utf-8")).encode()
    iv = os.urandom(16)
    ciphertext = AES.new(key, AES.MODE_CBC, iv).encrypt(pad(modified, 16))
    unsigned = header + iv + ciphertext
    result = unsigned + hmac.new(key, unsigned, hashlib.sha1).digest()
    output.write_bytes(result)
    output.chmod(0o600)
    return result


def csrf_meta(html):
    tag = BeautifulSoup(html, "html.parser").find("meta", attrs={"name": "CSRFtoken"})
    if not tag:
        raise RuntimeError("CSRF token not found")
    return tag["content"]


def authenticate(session, base, username, password):
    token = csrf_meta(session.get(base + "/", timeout=10).text)
    user = srp.User(username.encode(), password.encode(), hash_alg=srp.SHA256, ng_type=srp.NG_2048)
    name, public = user.start_authentication()
    challenge = session.post(
        base + "/authenticate",
        data={"CSRFtoken": token, "I": name.decode(), "A": binascii.hexlify(public).decode()},
        timeout=10,
    ).json()
    proof = user.process_challenge(
        binascii.unhexlify(challenge["s"]), binascii.unhexlify(challenge["B"])
    )
    answer = session.post(
        base + "/authenticate",
        data={"CSRFtoken": token, "M": binascii.hexlify(proof).decode()},
        timeout=10,
    ).json()
    if "error" in answer:
        raise RuntimeError(f"authentication failed: {answer['error']}")
    user.verify_session(binascii.unhexlify(answer["M"]))
    if not user.authenticated():
        raise RuntimeError("SRP verification failed")


def import_config(base, username, password, config_path):
    session = requests.Session()
    authenticate(session, base, username, password)
    token = csrf_meta(session.get(base + "/", timeout=10).text)
    load_hash = "VF" + hashlib.sha1(("VBNT-Z" + password).encode()).hexdigest()
    response = session.post(
        base + "/modals/settings/configuration.lp",
        data={"CSRFtoken": token, "action": "ConfigLoad", "loadhash": load_hash},
        timeout=15,
    )
    response.raise_for_status()
    page = session.get(base + "/modals/settings/configuration.lp", timeout=10).text
    match = re.search(r'form_data\.append\("CSRFtoken",\s*"([0-9a-f]+)"\)', page)
    if not match:
        raise RuntimeError("configuration upload token not found")
    with config_path.open("rb") as handle:
        response = session.post(
            base + "/modals/settings/configuration.lp?action=import_config",
            files={
                "CSRFtoken": (None, match.group(1)),
                "configfile": (config_path.name, handle, "application/octet-stream"),
            },
            timeout=60,
        )
    if response.status_code != 200 or "success" not in response.text.lower():
        raise RuntimeError(f"import rejected: HTTP {response.status_code}: {response.text[:200]}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("backup", type=Path, help="original password-protected VBNT-Z .bin backup")
    parser.add_argument("--output", type=Path, default=Path("CP1829SA73506102026-wps-root.bin"))
    parser.add_argument("--base-url", default="http://127.0.0.1:18100")
    parser.add_argument("--username", default="vodafone")
    parser.add_argument("--build-only", action="store_true")
    args = parser.parse_args()
    password = os.environ.get("UH_WEB_PASSWORD") or getpass.getpass("Router web/backup password: ")
    build_config(args.backup, args.output, password)
    print(f"Built signed configuration: {args.output}")
    if args.build_only:
        return
    import_config(args.base_url.rstrip("/"), args.username, password, args.output)
    print("Import accepted. Wait until the router finishes rebooting.")
    print("WHEN IT IS BACK: hold the physical WPS button for about 2 seconds, then release it ONCE.")
    print("After 5-10 seconds, SSH to root@192.168.1.254 using password: root")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
