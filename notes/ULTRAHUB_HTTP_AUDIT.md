# Vodafone Ultra Hub HTTP command-injection audit

Date: 2026-10-06 UTC

Target: VBNT-Z / DNA0130VDF-NZ, firmware 17.4.b.0380.

## Result

No working HTTP command injection was confirmed in the tested DDNS route.

The historically vulnerable Vodafone/Technicolor technique submits a command
after the DDNS domain, for example `valid.example;COMMAND`. On this router:

- Historical endpoint `/modals/dns-ddns.lp`: HTTP 404.
- Current endpoint `/modals/internet/dns_ddns.lp`: HTTP 200, but input rejected.
- Harmless proof payload attempted to create `/tmp/http_injection_proof`.
- The marker was not created.
- The DDNS UCI values were unchanged by the rejected request.

The test was authenticated and included a valid CSRF token.

## Why the old payload is blocked

`dns_ddns.lp` maps `ddnsDomain` through
`post_helper.validateStringIsDomainName`. That validator processes each DNS
label and permits only alphanumerics and hyphens. A semicolon-appended shell
command fails validation, and `onPost()` refuses to apply DDNS changes while
validation errors exist.

The DDNS shell backend contains numerous `eval` operations, so bypassing this
validation would still be security-sensitive. Username and password fields are
only length checked at the page layer, but the backend percent-encodes their
characters before building the provider URL; no injection was established
through those fields.

## Other reviewed routes

- Diagnostic ping and traceroute validate the target as an IP address or DNS
  name before setting the transformer path.
- Port mirroring parses `-i INTERFACE` and compares the interface against
  transformer-enumerated ATM/PTM interface names.
- nginx's startup `os.execute()` command uses a fixed state-directory string,
  not request data.

## Extended transformer review

The original AutoFlashGUI payload formats were reproduced with harmless marker
commands. All legacy endpoints are absent on this firmware:

- `/modals/diagnostics-ping-modal.lp`: 404
- `/modals/wanservices-modal.lp`: 404
- `/dyndns.lp`: 404

No `/tmp/http_injection_proof` marker was created.

Potentially dangerous backend designs were inspected:

- `rpc_policyrouting.ca` reads a command from `/tmp/policyrouting.txt`, replaces
  commas with spaces, and invokes the resulting variable. The HTTP page only
  generates an `ip rule add/delete` command with a validated source address.
  The insufficiently validated WAN-table value can add arguments to `ip rule`,
  but shell control operators introduced through variable expansion are not
  reparsed by `ash`; no OS-command execution was established.
- `igd_LANEthernetInterfaceConfig.ca` executes a value read from
  `/tmp/.lan_intf`. Its mapping constructs that value as `ifconfig KEY up/down`,
  where `KEY` comes from kernel-enumerated network-interface entries rather
  than an HTTP form value.
- `/etc/init.d/xdsl` uses `eval` around advanced DSL options. The installed NZ
  `xdsl.lp` page is read-only and does not expose those fields for POST.
- TR-069 certificate upload accepts traversal-like names ending in `.0`, but
  the upload is parsed as X.509 and then renamed to a hex subject-hash name.
  This deserves separate file-write/path validation hardening, but it did not
  provide a direct command-injection path in this review.

## Saved analysis material

- `ultrahub-http-audit.tgz` and extracted `ultrahub-http-audit/`
- `ultrahub-ddns-audit.tgz` and extracted `ultrahub-ddns-audit/`
- `ultrahub-http-params.txt`
- `probe_ultrahub_ddns_injection.py`

The audit was deliberately non-destructive. It does not prove the absence of
all vulnerabilities in native transformer mappings or services not reachable
from the web UI.
