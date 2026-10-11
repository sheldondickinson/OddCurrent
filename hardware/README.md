# David V1 — wiring is NOT approved

This is a provisional module-level allocation. Obtain the exact carrier model,
revision, schematic and pin labels first. Check onboard RGB LEDs, USB bridge,
regulator limits, straps and boot behaviour. N16R8 means 16 MB flash / 8 MB PSRAM,
not a unique board. Reserve GPIO26–37 conservatively for memory, 0/3/45/46 for
straps, 19/20 for native USB, 17/18 for expansion and 43/44 for logging.

| Output | Proposed GPIO | Provisional pixels |
|---|---:|---:|
| Protected status | 4 | 1–2 |
| Body: all decorative regions in one serial chain | 5 | 195 |
| INMP441 BCLK / WS / DOUT | 10 / 11 / 12 | L/R grounded, 3.3 V only |
| Power / scene / audio / recessed setup | 13 / 14 / 15 / 16 | active low to GND |

Check INMP441 breakout pin naming against its schematic; use local 100 nF
decoupling. Do not power the microphone from 5 V. It emits digital audio and
requires I2S timing/channel validation, not an analogue ADC input.

## Signal and power requirements

For **confirmed 5 V pixels only**, investigate two channels of SN74AHCT245 at
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
- [ ] Two outputs concurrently driven with mic + Wi-Fi + WSS + native UI.
- [ ] Scope data at last pixel, full white and audio stress; no dropped channels; six-output alternative separately tested.
- [ ] Supply sizing, measured current, fuses, gauge, injection and voltage drop.
- [ ] Thermal soak at enforced current limit inside assembled 450 mm enclosure.
- [ ] Cold/hot boot, brownout, supply-order and USB backfeed checks.
- [ ] Each button, false holds, Wi-Fi recovery and update lockout tested.
- [ ] Two phones / homes: AP QR, captive portal fallback, NFC and internet outage.
- [ ] Real pixel order and coordinates calibrated separately for both lamps.
- [ ] Secure boot / flash encryption / signed OTA threat model accepted.

Earlier printable David geometry is not proof of fit for this 450 mm build:
measure internal channels, base, LED carrier dimensions and microphone opening.

## Seller evidence, 2026-10-12

Owner supplied product images for a dual USB-C CH343P carrier with WROOM-1
N16R8 marking and an 1117-family regulator. The supplied pin diagram labels the
onboard RGB LED GPIO47; similar carriers often use GPIO48. Reserve both until
continuity identifies the actual connection. Header labels show all proposed pins. The graphic incorrectly implies every exposed
memory GPIO can be freely used; reserve GPIO35–37 for octal PSRAM. No carrier
schematic or exact revision was supplied, so continuity, regulator capacity and
USB/external-5V backfeed remain open. GPIO6–9 are free in the two-output build.
Do not split the body data signal into parallel branches: regions use serial
physical indexes, measured sub-zone ranges and/or the calibrated XY map.

## Pixel report

Owner reports **WS2811 seed pixels, 5 V**, 2026-10-12. This establishes the
intended supply class, not measured current, channel order or bit timing. Confirm
800 kHz versus 400 kHz against the actual product/datasheet, test R/G/B individually,
and measure full-white current on a spare sample before final PSU/fuse sizing.

## Bare-board evidence, 2026-10-12

One owner-confirmed USB-only sample reports ESP32-S3 rev0.2, 16 MB flash and
8 MB embedded PSRAM. Its full pre-install flash was privately preserved and
device-digest verified before a clean development install. Bootloader at0x0,
partition table at0x8000 and application at0x10000 were readback verified. Four
native serial JSON responses reported WLED16.0.1, zero LEDs and hardware-ready0,
8,287,687 bytes free PSRAM and at least223,060 bytes free heap. Uptime increased
46→56s. This does not validate the carrier power circuit, any output pin signal,
INMP441, switches, Wi-Fi/WSS, power cycles or thermal operation. Factory identity
is not imported. Both gift registrations remain offline/never connected.

The artifact’s actual partition table uses two3 MiB app slots (app0 at0x10000,
app1 at0x310000), filesystem at0x610000 and coredump at0xff0000. Read the actual
artifact table before flashing; do not assume an older upstream CSV matches.
The install used normal Espressif esptool checks without force or eFuse writes.
