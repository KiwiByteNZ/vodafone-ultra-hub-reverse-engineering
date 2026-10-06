# Vodafone Ultra Hub Plus fingerprint

Collected locally on 2026-10-06 UTC from the user-owned router.

## Identity

- Board/system: Technicolor VBNT-Z
- Product profile: Vodafone NZ DNA0130VDF-NZ
- Hostname: `ultraplus.hub`
- LAN address: `192.168.1.254/24`
- Ethernet MAC: `A4:91:B1:64:B2:48`
- Wi-Fi MAC: `A4:91:B1:64:B2:49`
- OS: OpenWrt Chaos Calmer 15.05.1, Technicolor `Mauve (17.4.b)`
- Firmware: `17.4.b.0380-0841006-20211013062849-f8c0cc38e6b00eb1da718a7506df0cf999c8d80e`
- Kernel: Linux 4.1.38, SMP PREEMPT, built 2019-10-29
- Architecture: MIPS, dual Broadcom BMIPS4350 V8.0 processors
- Bootloader: 2.0.100

## Capacity

- RAM: 252056 KiB total; no swap
- Read-only firmware filesystem: 24.8 MiB
- Writable overlay: 31.5 MiB, 6.1 MiB used
- Attached `/dev/sda1`: 28.7 GiB, 4.5 GiB used

## Listening TCP services

| Address | Port | Process / purpose |
|---|---:|---|
| `192.168.1.254` | 22 | Dropbear SSH 2017.75 |
| `192.168.1.254`, localhost | 53 | dnsmasq 2.78 DNS |
| all IPv4/IPv6 | 80 | nginx 1.10.3 HTTP |
| all IPv4/IPv6 | 443 | nginx HTTPS |
| all IPv4/IPv6 | 8080 | nginx alternate HTTP |
| all IPv4/IPv6 | 65443 | nginx alternate HTTPS |
| all IPv4/IPv6 | 51005 | `cwmpd` / TR-069 service |
| all IPv4 | 6050 | `mmpbxd` |
| localhost | 55555 | nginx internal listener |

Listening on all addresses does not by itself prove WAN exposure; firewall
policy still controls reachability. SSH is configured for the LAN interface.

## SSH server identity

- Key type: RSA
- MD5 fingerprint: `12:c3:33:fb:ac:6b:00:b1:d9:ba:2d:4d:60:36:8e:a9`
- Server: Dropbear 2017.75
- Legacy compatibility required: RSA host key and
  `diffie-hellman-group14-sha1` key exchange

## Security observations

- The operating system, kernel, SSH, DNS, and web-server builds are old.
- The selected root password is short and should be considered temporary.
- Keep SSH restricted to the trusted LAN and do not expose ports 22, 51005,
  6050, 8080, or 65443 to the public internet.
- The device currently showed only its directly connected `192.168.1.0/24`
  route during collection.
