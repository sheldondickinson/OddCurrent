# Microphone testing and measured 2D mapping

## Operator dashboard

An explicitly allowlisted administrator lands at `/admin` after sign-in. Owners
and guests retain the lamp controls. The fleet shows online/offline/never-connected
state, last heartbeat, reported local IPv4 address, firmware, heap/PSRAM, RSSI,
reconnects, uptime, errors, claim state and mapping readiness. An IP is a last
reported LAN address, not a public endpoint. It is absent from non-admin views.

Request diagnostics, identify (five seconds), restart and locate a body pixel
(three seconds) use administrator-only, CSRF-protected, expiring commands. Restart
preserves identity and Wi-Fi. No commands queue while offline. Read receipts before
calling an action successful. Current firmware must report maintenance protocol1;
older firmware displays the unsupported state. Diagnostic downloads contain local
network information and should remain private. No firmware release, factory reset,
Wi-Fi reset or arbitrary WLED/GPIO passthrough is exposed remotely.

## Test the INMP441

David uses Generic I2S input: VDD3.3V, GND common, SCK/BCLK GPIO10, WS GPIO11,
SD/DOUT GPIO12, L/R GND (left channel), no MCLK. LED power stays on its own5V rail.
The live WLED configuration must show `digitalmic.type=1` and
`digitalmic.pin=[12,11,10,-1]`. If these settings change, save and restart the
controller before testing. Leave AudioReactive UDP sync off to test the local mic.

1. Open the selected device in Admin and expand **Microphone test**. Enable Music;
   this turns the light on at a low test brightness. Audio processing must be on.
2. Stay quiet for about10seconds and note the level/window peak. Then speak or clap
   near the mic for about10seconds. Finally stop for another10seconds.
3. A useful result rises with sound and falls again in quiet. A frozen0 or255,
   constant noise, or an animated effect without corresponding meter changes does
   not prove the microphone works. WLED effects can simulate audio when a live
   audio module is unavailable; this meter reads the real module without that
   simulation fallback.
4. If necessary, use native WLED **Config → Usermods → AudioReactive** to adjust
   squelch (noise gate), gain and AGC. Change one setting at a time; record the quiet
   and sound observations. The OddCurrent sensitivity slider changes input level,
   not pin selection or squelch. Avoid starting with maximum gain on an untested mic.
5. Disable Music or choose another scene afterwards. Repeat with Wi-Fi/cloud and
   both LED outputs active; check for resets, pinned noise or dropouts.

The dashboard reports only relative processed level0–255 and a window peak,
updated about every5seconds while audio is active. A clap may appear in the next
window. The local `/json/info` OddCurrent fields offer faster read-only checks.
These are not raw audio, recordings, calibrated dB or an automatic pass/fail test.

References: [WLED AudioReactive](https://kno.wled.ge/advanced/audio-reactive/),
[pinned AudioReactive data contract](https://github.com/wled/WLED/blob/29b389df1c1aaec6ff53aea742d17063b985906c/usermods/audioreactive/audio_reactive.cpp).

## Measure the 2D map

Mapping follows the **final installed pixel positions**, not a guessed statue
outline. Each physical lamp needs its own measurements if routing differs.
Two status pixels use physical WLED indices0–1. Body-local indices0–194 correspond
to WLED indices2–196. Status remains separate and follows body colours in normal
operation; it never occupies a map cell or anatomical mask.

1. Photograph the assembled lamp from the chosen front view and mark the data-flow
   direction. Confirm the body count with walking pixels before recording positions.
2. In Admin choose the lamp, then **Open this device’s map editor**. Start with a
   suitable grid (e.g.24×48), status count2 and actual body count195. Coordinates
   start at the top-left; x increases right and y down. Increase resolution if
   distinct pixels would collide; each cell holds one physical pixel.
3. Set body index0 and use **Locate selected body pixel**. The firmware temporarily
   lights that physical body pixel, with other body pixels dark, then restores the
   effect after three seconds. Ignore the two status pixels when locating indices0–1,
   because they can mirror those body pixels. Locate works in physical order even
   after a map exists.
4. Choose the anatomical zone and click the measured grid cell. The body index
   advances. Continue through every body pixel. Empty cells remain empty. If front
   and rear pixels overlap in projection, use a finer grid or an explicitly recorded
   unfolded layout; do not silently assign duplicate cells or invented measurements.
5. Export measurements frequently. Import resumes a saved file; do not close an
   unsaved browser tab. Keep the original measurements per serial number.
6. Generate and validate the files from the repository root:

   ```sh
   python scripts/profiles.py profiles/david-v1.json \
     --calibration david-measurements.json --out output/david-map
   ```

   Every body pixel must occur exactly once, coordinates and zones must be valid,
   and no status index is allowed. This produces `ledmap.json` and `regions.json`.
   Keep the generated map compact: pinned WLED streams the exact token `"map":[`.
   Pretty-printing it with a space after the colon breaks that upstream loader.
7. On the lamp's local network, privately back up `cfg.json`, presets and existing
   map files using native WLED's file editor (`/edit`). Upload only the generated
   `ledmap.json` and `regions.json`, then restart. Do not replace Wi-Fi security or
   factory identity. The generated default map's width/height enables WLED's2D
   projection; confirm a full-width/full-height2D segment in the native UI.
8. Confirm `zones_ready` and `xy_ready` in diagnostics, then test left-to-right and
   top-to-bottom sweeps and each anatomical zone. Correct orientation/positions in
   the measurements and regenerate if needed. Recheck standby/fault status behaviour.

A complete validated measured map can load in explicitly enabled prototype mode;
this does not assert final electrical/thermal acceptance. The full configuration
generator still requires its independent physical gates. No real David map is
bundled: software map tests use clearly identified synthetic fixtures only.
For rollback, restore the private pre-map config/presets and previous map files,
then restart. Keep the flat1D state until the measured projection is accepted.

Reference: [WLED custom mapping](https://kno.wled.ge/advanced/mapping/).
