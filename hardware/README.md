# David V1 — wiring is NOT approved

This is a provisional module-level allocation. Obtain the exact carrier model,
revision, schematic and pin labels first. Check onboard RGB LEDs, USB bridge,
regulator limits, straps and boot behaviour. N16R8 means 16 MB flash / 8 MB PSRAM,
not a unique board. Reserve GPIO26–37 conservatively for memory, 0/3/45/46 for
straps, 19/20 for native USB, 17/18 for expansion and 43/44 for logging.

| Output | Proposed GPIO | Provisional pixels |
|---|---:|---:|
| Protected status | 4 | 1–2 |
| Left arm / hand | 5 | 20 |
| Right arm / hand | 6 | 20 |
| Left leg / foot | 7 | 28 |
| Right leg / foot | 8 | 27 |
| Core: torso/pelvis then head/hair | 9 | 100 |
| INMP441 BCLK / WS / DOUT | 10 / 11 / 12 | L/R grounded, 3.3 V only |
| Power / scene / audio / recessed setup | 13 / 14 / 15 / 16 | active low to GND |

Check INMP441 breakout pin naming against its schematic; use local 100 nF
decoupling. Do not power the microphone from 5 V. It emits digital audio and
requires I2S timing/channel validation, not an analogue ADC input.

## Signal and power requirements

For **confirmed 5 V pixels only**, investigate six channels of SN74AHCT245 at
5 V, A→B DIR fixed high, OE held disabled until supplies and MCU are stable,
100 nF at VCC and a short common-ground return. A seventh/eighth unused channel
must not float. Put a series resistor near each data driver; choose its final
value from scope/signal tests. Add data pulldowns and verify no parasitic powering
with either supply absent. This part's datasheet does not by itself establish safe
partial-power behaviour for the entire circuit; use an appropriate isolation/OE
power-good design if tests require it. A voltage divider is not a level shifter.

Do not route pixel current through the ESP board, USB cable, breadboard or thin
data connectors. Fuse branches close to the external isolated SELV PSU. Use
polarised keyed harnesses, strain relief and labels. No mains inside the statue.
Avoid simultaneously feeding USB and external 5 V unless the carrier's power
OR-ing/backfeed protection is verified. Test USB access and base serviceability.

Conditional worst case for 197 × 60 mA RGB pixels: **11.82 A / 59.1 W at 5 V**,
before controller and margin. This is a worksheet assumption, not measured draw
or a PSU purchase recommendation. A firmware limit does not replace fuses.

## Release prerequisites

- [ ] Exact carrier schematic/pin continuity and module marking recorded.
- [ ] Actual chipset, voltage, colour order and per-pixel current confirmed.
- [ ] Six outputs concurrently driven with mic + Wi-Fi + WSS + native UI.
- [ ] Scope data at last pixel, full white and audio stress; no dropped channels.
- [ ] Supply sizing, measured current, fuses, gauge, injection and voltage drop.
- [ ] Thermal soak at enforced current limit inside assembled 450 mm enclosure.
- [ ] Cold/hot boot, brownout, supply-order and USB backfeed checks.
- [ ] Each button, false holds, Wi-Fi recovery and update lockout tested.
- [ ] Two phones / homes: AP QR, captive portal fallback, NFC and internet outage.
- [ ] Real pixel order and coordinates calibrated separately for both lamps.
- [ ] Secure boot / flash encryption / signed OTA threat model accepted.

Earlier printable David geometry is not proof of fit for this 450 mm build:
measure internal channels, base, LED carrier dimensions and microphone opening.
