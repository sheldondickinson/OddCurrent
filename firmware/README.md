# WLED / OddCurrent development firmware

Pinned upstream: WLED 16.0.1,
`29b389df1c1aaec6ff53aea742d17063b985906c`. The selected compile target is
QIO 16 MB flash and OPI 8 MB PSRAM. It targets the CH343P UART USB connector
(`ARDUINO_USB_CDC_ON_BOOT=0`); native USB is not assumed to be the serial channel.

Button diagnostics are read-only native serial JSON info: `{"v":true}` returns
`info.oddcurrent.button_inputs` for GPIO13–16 (raw level, active-low pressed state
and allocation success). It remains available during the virgin GPIO16 service
hold; the factory credential import still requires that hold. Run
`python scripts/button_monitor.py --port <confirmed-port> --seconds 60`, then
press and release each external button briefly, one at a time. Avoid long setup
holds during monitoring because the existing 5/15-second recovery actions apply.
The monitor never sets GPIO directions, writes configuration or exposes secrets.
Digital levels are not voltage, continuity, waveform or debounce measurements.
Confirm actual carrier and USB connector behaviour before uploading.

The upstream default Tasmota framework omits `WiFiClientSecure`. This target uses
the upstream-documented Espressif32 6.13.0 framework option (Arduino 2.0.17 /
IDF 4.4.7), with explicit certificate-verifying WebSockets dependencies.

Stock WLED's default GPIO16 conflicts with David's recessed setup button. This
target disables WLED's automatic default-bus creation until a validated bus config
is installed, so a virgin image cannot drive the recovery switch. Native output
configuration remains available through the local UI. No wiring is approved by
this compile-time allocation.

The extension keeps WLED's native web UI, mDNS and audio-reactive usermod. It adds
certificate-verified outbound WebSockets, expiring session-bound commands,
four-button gestures and physical status protection after WLED's XY mapping.
No credentials are embedded in the image. Factory NVS identity is separate from
home Wi-Fi and survives the recessed 15-second Wi-Fi-clear gesture. Serial
provisioning accepts only a virgin identity while the service button is held.
Electrical activation is **off by default**. After private identity and Wi-Fi
provisioning, the cloud transport can report diagnostics while hardware is disabled;
lighting commands still fail the hardware-ready guard. The public build is not
tamper-proof.

Four bounded hooks are checked by the build script:

1. After pixel mapping, immediately before `BusManager::show()`, drive physical
   status bus0. While on, its two pixels mirror the first two final body pixels
   at the body's global brightness, including native/audio/realtime/region effects.
   While off, they breathe alternately in blue/violet at bounded status brightness.
   A device fault overrides either mode with red. Wi-Fi/cloud loss does not take
   over a running local effect. Status indexes remain excluded from calibration.
2. Before native serial processing, permit physical-button-gated factory import.
   After factory identity exists the native serial handler remains available.
3. On the password-protected AP interface, the root serves a minimal OddCurrent
   setup form with network scanning, a per-boot CSRF token and connection status.
   Home-LAN clients retain the native WLED UI.
4. Virgin-image default output creation is disabled. WLED would otherwise try
   another free pin when its configured default is invalid, so an invalid pin
   marker alone is insufficient. Explicit validated bus configurations still load.

Test native UI behaviour and all realtime modes on the actual image; source
placement is not hardware evidence. WLED's default onboard output is not a final
David configuration. Do not wire outputs or enable `hardware_ready` until the
carrier/pixel/electrical gates pass and the actual bus config is installed.

## Buttons

| Button | Short | Long | Double |
|---|---|---|---|
| GPIO13 | toggle / restore brightness | repeat brightness; reverse at bounds | night |
| GPIO14 | next curated scene | previous curated scene | favourite (Gallery default) |
| GPIO15 | toggle music | cycle sensitivity | next music palette |
| GPIO16 recessed | none | 5 s AP; 13 s warning; 15 s Wi-Fi-only clear | none |

35 ms debounce, 350 ms double interval, 700 ms normal long press and 250 ms repeat.
Update lockout suppresses gestures. Host policy tests cover transitions; the
real switches, interruption timing and status brightness still require bench tests.

## Build / USB recovery

```sh
PATH="$PWD/.firmware-venv/bin:$PATH" .firmware-venv/bin/python scripts/build_firmware.py
```

Development artifacts are ignored under `firmware/build/`. Save exact binary
hashes, build environment and upstream revision. No automatic flashing command is
run. Recover via the carrier's USB-to-UART port: hold BOOT, pulse RESET, release
BOOT, use Espressif esptool for the validated S3 target and this image's actual
partition offsets. Preserve NVS / filesystem first when factory identities exist.
Do not erase all flash to fix Wi-Fi. Inspect board power while USB is connected.

Use `scripts/serial_provision.py --port <confirmed-port> --factory <private-file>`
with the recessed service button held on a virgin device. It waits for an explicit
firmware acknowledgement and does not display values. This pathway is untested
until a physical device is attached. After identity import, generate the validated
local config with `scripts/wled_config.py`. Import/review the fragment rather than
overwriting WLED's full configuration. `sec.json` and factory NVS stay private.

## Mapping / limitations

The pixel editor exports measurement input. `scripts/profiles.py` checks every
decorative physical index, duplicate grid cells, range and status exclusion, then
writes `ledmap.json` (`-1` gaps) and `regions.json`. Configure WLED's 2D dimensions
to match and upload both on the trusted LAN. Whole-body animations use native
WLED mapping/effects. Independently selected static/colour/pulse/spectrum region
masks apply after projection. Independent **music per region** remains rejected
pending a tested segment/audio adapter. The generic platform retains a six-output
profile; only the selected two-output image is built by this target.

Automatic signed cloud OTA, resumable credential rotation, persistent favourite
editing remain release work. OddCurrent saves settled scene/light state in
wear-levelled NVS after ten seconds, at most once per minute. Abrupt power loss
before that interval restores the previous saved state. Hot/cold restore behaviour
and flash-wear expectations still require bench acceptance. Native OTA needs a unique strong private
password. Secure boot/flash encryption and the watchdog-disabled upstream S3
default require separate review. Do not ship this development image unchanged.
