# Validation record — 12 October 2026

This is a development milestone, **not a shipping certificate**. All synthetic
values and coordinates are fixtures/simulation, not David readings. Private
operating facts and endpoints remain in the owner’s canonical registry.

| Check | Actual result / limitation |
|---|---|
| Backend/profile/factory/backup tests | 36 pytest tests passed locally on Python 3.12 and in CI; no physical device |
| Firmware policy | Host C++ tests passed for debounce, gestures, setup holds, update lockout, status priority, expiry and replay |
| Public source | Tracked-file scan passed; private runtime/factory files excluded; owner endpoints and paths absent |
| Backend dependency audit | No known vulnerabilities returned by dated requirements audit |
| Desktop/mobile UI | Browser-rendered simulator login and Sunset acknowledgement; 390 px viewport has 390 px document width |
| Calibration editor | Starts with zero measured coordinates; completeness/duplicate/status-exclusion validation implemented |
| GitHub CI | Software, firmware and restrictive-checkout container jobs all passed for `828f650ac1b20089392ec4237166831161cffe8f`, [run 38185006643](https://github.com/sheldondickinson/OddCurrent/actions/runs/38185006643) |
| ESP32 compile | Pinned WLED 16.0.1 S3 N16R8 target compiled; downloaded binary hashes matched CI; unsigned development artifacts only |
| Hosted application | Restrictive read-only production container running; HTTPS health and anonymous API denial verified; dedicated workload read accepted and unrelated record read denied |
| OIDC | Real owner browser code/PKCE callback completed; operator fleet displays both unclaimed, offline lamps. Recipient and unrelated-account browser acceptance remains pending |
| Public device transport | Temporary synthetic fixture exercised certificate-verified Cloudflare WSS upgrade, invalid credential rejection, telemetry, session-bound command/ACK, replay rejection and offline rejection. Fixture removed |
| SQLite recovery | Nightly online backup enabled; actual production backup restored separately with integrity, two unclaimed identities and sequences checked. Off-host disaster restore not exercised |
| Factory material | Two unique private identities, setup QR SVGs, claim inserts and HTTPS NFC destinations generated; credentials/claims stored hash-only on server; owner-encrypted archive round-trip checked |
| USB-only board | One owner-connected bare board identified as S3 rev0.2, 16 MB flash/8 MB PSRAM; full pre-install flash backed up and digest-verified, encrypted round-trip checked; bootloader/partition/app readback verified after development install |
| Bare-board boot | Four native WLED 16.0.1 serial JSON responses, uptime46→56s, free PSRAM8,287,687 bytes, minimum free heap223,060 bytes; zero LEDs, hardware activation disabled, no factory identity/cloud connection |
| Direct-drive design | Owner accepts GPIO4/5 direct 3.3 V drive, no translator, on12 October2026. This is a design decision; actual signal reliability remains untested |
| Hardware/peripherals | No pixels, microphone, buttons or external power attached. Exact carrier/power circuit and all peripheral/electrical/thermal acceptance remain pending |
| Onboarding/QR/NFC | AP-only portal and tools implemented; destination HTTP routes exist. Real phones, tags, captive portal and Wi-Fi association untested |
| OTA/tamper resistance | Cloud updates disabled; signing, rollback, secure boot and flash encryption not accepted |

The hosted runtime uses the previously verified backend commit `ddf777b`; subsequent
changes through `828f650` affect firmware/factory tooling, not the deployed backend.
The USB board is unassigned and its factory namespace is virgin; the two real
registrations have never connected. No synthetic test values were
written to their device records.

The USB result is a short observation, not power-cycle, network, peripheral or
soak acceptance. The pre-install flash remains private. No eFuses were burned and
no secure-boot/encryption bypass was used. NVS/filesystem were cleared only after
the full recovery image matched the device digest; gift identities have not been
imported. Physical-button-gated serial provisioning is still required.

## Release blockers

1. Exact carrier revision/power schematic or continuity and USB backfeed proof.
2. Pixel timing (400/800 kHz), colour order, current, direct-drive harness/fuse/PSU
   design and both-lamp qualification per [prototype plan](../hardware/prototype-testing.md).
   The accepted logic-margin trade-off is not a requirement to add a translator.
3. Two simultaneous outputs + INMP441 + WSS + native UI; reconnect/heap and
   local-control latency. Six-output alternative requires a separate bench test.
4. Both real maps and anatomical masks, hot/cold boots, switch gestures,
   AP recovery, false holds and update interruption.
5. Recipient-only account/permission acceptance, device credential rotation and
   off-host app recovery. Gift owners may be assigned later; no invitations sent.
6. Physical identity import, shipping NFC write/readback, iPhone/Android onboarding
   at two homes, internet-outage behaviour and strong native OTA protection.
7. Signed firmware/recovery plan; review upstream npm build-tool advisories,
   the S3 watchdog default and remaining features (schedules/favourite editing).

No source test can close a physical gate. `scripts/profiles.py --wiring` deliberately
rejects the present profile. Final PSU selection must use measured load; the
conditional 60 mA example remains 11.82 A / 59.1 W for 197 pixels, not a measured
requirement. Cloudflare Tunnel runs on the server; the ESP32 only opens outbound
certificate-verified WSS. Native WLED UI and audio stay local by design, with actual
internet-outage acceptance still pending bench tests.
