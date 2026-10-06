# Vodafone Ultra Hub Plus root checkpoint

Date: 2026-10-06 UTC

Target: Technicolor VBNT-Z / Vodafone DNA0130VDF-NZ at `192.168.1.254`.

## Confirmed state

- Signed configuration import succeeded.
- Dropbear SSH is enabled on the LAN interface only, TCP port 22.
- Root password authentication and root login are enabled.
- Root login reaches BusyBox `ash`; `id` returned `uid=0(root) gid=0(root)`.
- `/etc/passwd` contains `root:x:0:0:root:/root:/bin/ash`.
- The temporary WPS command handler was restored and committed as
  `wps_button_pressed.sh` after root access was confirmed.
- WAN Dropbear settings were not enabled.

## Important correction

The working WPS handler replaces the shell pathname alone:

```sh
sed -i "s#/bin/restricted_shell#/bin/ash#" /etc/passwd; /etc/init.d/dropbear restart
```

Do not search for `root:/bin/restricted_shell`: normal passwd fields occur
between the account name and login shell, so that expression does not match.

## Files

- `vbnt-z-wps-root.py` - builds, signs, and uploads the configuration.
- `vbnt_z_mysrp.py` - web authentication support.
- `vodafone-ultrahub-config-20261006-062548.bin` - untouched encrypted backup.
- `vodafone-ultrahub-config-20261006-062548-decrypted.txt` - decrypted backup.
- `CP1829SA73506102026-wps-root.bin` - corrected generated configuration.

Passwords are intentionally omitted from this checkpoint.

## Password verification

The temporary/default root password was changed at the user's request and a
fresh SSH authentication was successful. The password itself is intentionally
not recorded here. The router warned that the chosen value is short.
