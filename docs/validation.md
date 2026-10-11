# Validation record — 12 October 2026

This is a development milestone, **not a shipping or deployment certificate**.
All synthetic values and coordinates are fixtures/simulation, not David readings.

| Check | Actual result / limitation |
|---|---|
| Backend/profile/factory/backup tests | 35 pytest tests passed locally on Python3.12; no physical device |
| Firmware policy | Host C++ tests passed for debounce, gestures, setup holds, update lockout, status priority, expiry and replay |
| Public source | Tracked-file scan passed; no private endpoint/path/key patterns, ignored factory/runtime files excluded |
| Backend dependency audit | No known vulnerabilities returned by dated requirements audit |
| Desktop/mobile UI | Browser-rendered, simulator login and Sunset command acknowledgement checked; 390px viewport has390px document width |
| Calibration editor | Starts with0 measured coordinates; exports input for completeness/duplicate/status validation |
| SQLite recovery | Online backup restored owner, device and sequence in independent temporary database with integrity check |
| GitHub software CI | Passed initial33-test milestone, C++ policy, JS syntax and public-source checks; final revision CI must be read back |
| ESP32 compile | Under validation; unsigned development artifact only after successful CI/build |
| Docker service | Portable container prepared; local daemon unavailable, no running production container claimed |
| Real OIDC sign-in | Requires dedicated issuer/client/callback and allowed/denied account browser acceptance |
| Hardware | None attached/flashed. Seller board photos and owner-reported5V WS2811 are specification evidence only |
| Onboarding/QR/NFC | Tools and AP-only portal implemented; real phones, tags and secure Wi-Fi association untested |
| OTA/tamper resistance | Cloud updates disabled; signing, rollback, secure boot and flash encryption not accepted |

## Release blockers

1. Exact carrier revision/power schematic or continuity and USB backfeed proof.
2. Pixel timing (400/800kHz), colour order, current, harness/fuse/PSU design and soak.
3. Two simultaneous outputs + INMP441 + WSS + native UI; failure/reconnect/heap and
   local-control latency. Six-output alternative requires a separate bench test.
4. Both real maps and anatomical masks, firmware hot/cold boots, switch gestures,
   AP recovery, false holds and update interruption.
5. Dedicated production app identity/secret scope, confirmed HTTPS origin and
   server ingress, actual account/permission and device end-to-end acceptance.
6. Per-device identity provisioning/rotation, shipping NFC destinations and readback,
   real iPhone/Android onboarding at two homes, strong native OTA protection.
7. Signed firmware/recovery plan; review WLED's upstream npm build-tool advisories,
   the S3 watchdog default and remaining future features (schedules/favourite editing).

No source test can close a physical gate. `scripts/profiles.py --wiring` deliberately
rejects the present profile. Final PSU selection must use measured load; the
conditional60mA example remains11.82A/59.1W for197 pixels, not a measured requirement.
