# OddCurrent

**Make the unexpected move.** A reusable local-first connected-creations platform,
starting with David: a 450 mm illuminated sculpture made as two gifts.

**Development milestone, not a shipping release.** The software is implemented and
tested locally and in CI, with a running owner-hosted application. Hardware wiring
approval, real phone onboarding, signed firmware and physical verification remain
explicit gates. Read
[`docs/validation.md`](docs/validation.md) for actual test evidence.

David V1 now uses **two LED outputs**, per the owner's revised requirement:
GPIO4 for 1–2 protected status pixels, GPIO5 for one serial 195-pixel decorative
chain. Anatomical zones and sparse whole-body XY mapping are logical. A provisional
six-output alternative remains in `profiles/`; it is not the selected gift build.
David V1 uses direct 3.3 V GPIO drive with no translator, by owner decision; the
logic-margin trade-off is accepted and actual reliability remains a shipment gate.
See the [wiring diagram](hardware/david-v1-wiring.md) and
[prototype plan](hardware/prototype-testing.md). Owner reports 5 V WS2811 seeds. Actual timing, colour order, current and carrier
power schematic remain unconfirmed.

## Run locally

```sh
python3.12 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q
c++ -std=c++17 tests/policy_test.cpp -o /tmp/oddcurrent-policy-test
/tmp/oddcurrent-policy-test
.venv/bin/python -m server --demo
```

Open `http://127.0.0.1:8787` and choose **Try the local simulator**. Simulation
is loopback-only, visibly labelled and absent from production configuration.
No lamp readings or electrical behaviour are represented as measured.

## Build firmware

```sh
python3.12 -m venv .firmware-venv
.firmware-venv/bin/pip install -r requirements-firmware.txt
PATH="$PWD/.firmware-venv/bin:$PATH" .firmware-venv/bin/python scripts/build_firmware.py
```

The script verifies WLED revision, copies the usermod, applies two checked hooks
and builds a development N16R8 image. WLED retains its native UI/audio/discovery.
Firmware-specific upstream licensing remains applicable; do not relicence WLED.
OddCurrent's original files are MIT. Consult [`firmware/README.md`](firmware/README.md)
before flashing. Compilation is not peripheral, USB or power validation.

Install `requirements-firmware.txt` in a separate `.firmware-venv` environment
and put its `bin` directory on PATH for the firmware command. PlatformIO's local
UI dependencies constrain Uvicorn, so it must not share the backend environment.

## Project guide

| Area | Purpose |
|---|---|
| `firmware/` | Pinned WLED adapter, button/command policy, protected status hook |
| `server/` | OIDC, sessions, ownership, invitations, SQLite, outbound device WSS |
| `web/` | Responsive David controls, diagnostics, permissions and map editor |
| `profiles/` | Versioned hardware capabilities and measurement schema |
| `hardware/` | Provisional pins, two-lamp BOM, power worksheet and physical gates |
| `branding/` | Editable supplied SVG brand assets and brand guide |
| `scripts/` | Firmware, factory identity/QR, serial import, map validation, backup |
| `tests/` | Access/transport/map/manufacturing and host-compiled firmware policy |

Start with [architecture](docs/architecture.md), [wiring prerequisites](hardware/README.md),
[manufacturing/onboarding](docs/provisioning.md), [protocol](docs/protocol.md) and
[deployment/recovery](docs/deployment.md). Portable examples use reserved domains.
Keep actual operating endpoints, secret grants and recovery material in private
infrastructure documentation; the public repository contains no production values.
