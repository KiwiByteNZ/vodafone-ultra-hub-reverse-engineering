# Vodafone Ultra Hub reverse engineering

Reverse-engineering notes, configuration tooling, extracted service files, and
lab scripts for the Vodafone New Zealand Ultra Hub Plus:

- Product: `Vodafone-DNA0130VDF-NZ`
- Technicolor platform: `VBNT-Z`
- Firmware family: Mauve `17.4.b`
- Embedded operating system: OpenWrt/Technicolor NG Gateway

## Repository layout

- `notes/` — fingerprint, HTTP audit, and persistent-root checkpoint
- `tools/` — signed configuration, SRP, DDNS audit, and LED scripts
- `configs/` — encrypted/decrypted configuration snapshots and root-enabled
  variants
- `audits/` — extracted HTTP, DDNS, Transformer, service, and filesystem data
- `CREDENTIALS.md` — credentials retained at the repository owner's request

## Root access

The signed configuration workflow enables LAN-only Dropbear SSH and changes the
root login shell to BusyBox `ash`. See `notes/ULTRAHUB_ROOT_CHECKPOINT.md` and
`tools/vbnt-z-wps-root.py`.

## Scope exclusions

This repository contains only Vodafone Ultra Hub/Technicolor VBNT-Z material.
Research for other routers, modems, extenders, and set-top boxes is excluded.

## Warning

This repository contains device-specific configuration and credentials. Use it
only with hardware you own or are authorized to assess. Publishing it exposes
the included passwords and configuration secrets.
