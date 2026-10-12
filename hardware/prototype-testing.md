# David V1 prototype testing and shipment gate

Baseline: GPIO4 directly drives 1–2 status pixels; GPIO5 directly drives the body
chain. No logic-level translator. The owner accepts the 3.3 V logic-margin
trade-off. Follow the [wiring plan](david-v1-wiring.md); tests assess this chosen
build. No pixel/peripheral reliability results have been recorded yet.

## 1. Carrier and power path, before energising a pixel harness

- Record actual module/carrier markings and header continuity for GPIO4/5,
  GPIO10–16, 3.3 V, 5 V and GND. Reserve uncertain onboard RGB GPIO47/48.
- With supplies disconnected, trace the regulator/input and USB power paths using
  schematic, continuity and diode measurements. Identify any path between external
  5 V and either USB VBUS. Record limits for board rail, regulator and connectors.
- Use the USB-only controller / independent LED PSU topology for initial tests:
  common GND, LED +5 V kept off the controller. Validate the final controller
  power/service arrangement separately before connecting USB and external board power.
- Check polarity, shorts, branch protection, connector/gauge selection and ground
  returns. Use a current-limited LED source with a conservative limit for the small
  sample; assign real settings from the sample test load, not the full-body estimate.
- Confirm no parasitic powering through DIN and no unsafe reverse feed for each
  intended power state. Begin with LED supply on before an enabled data source;
  disable/hold data low before removing LED power. Test other sequences under
  controlled conditions after tracing the paths, not by blindly hot-plugging.

Carrier/backfeed results remain open. The direct-drive decision is already settled.

## 2. Small-sample output tests

After the preceding checks, connect the exact status count and a small sample of
body pixels from the intended lot. Save a separate, minimal local WLED bench
configuration with GPIO4 as bus0 and GPIO5 as bus1, measured counts and a low
brightness/current limit. Record protocol400/800 kHz and colour order from sample
results. Keep decorative mapping out of this first test.

Progressively enable only the bench outputs being tested through the trusted local
configuration. The existing image starts with zero buses and hardware-ready0.
Keep production profile gates false until their corresponding checks actually pass;
do not fabricate calibration or set all gates true to make the generator run.
Cloud lighting stays disabled until electrical activation is justified; private
factory/Wi-Fi provisioning can be tested separately with outputs disabled.

Test each output alone, then together: off, static R/G/B, white at the bench limit,
walking pixel, alternating bits/colours and fast scene changes. Check exact indexing
and any unexpected flashes during reset, boot and idle. Scope the GPIO and DIN of
the first pixel on **each** output relative to local pixel GND; capture high/low
levels, pulse widths, rise/fall, ringing and ground offset. Check downstream data
where a failure appears; use a short probe ground to avoid a misleading capture.

Record link/series-resistor/pulldown populations and controller-to-first-pixel cable
length. Compare passive candidates only against repeatable observations; recheck
high-level margin and pulse shape after adding resistance or a pulldown. Keep the
accepted architecture unless fault evidence warrants a proposed correction.

## 3. Full harness and simultaneous peripherals

- Progress to the actual approximately195 body pixels plus1–2 status pixels. Route
  the first-pixel leads as short as practical; use the final connectors, wire and
  base layout, not a shorter surrogate. Confirm actual total196–197 or revise counts.
- Measure current and rail voltage at distribution, both first pixels, body end and
  injection points under recorded patterns/current limits. Choose PSU/injection,
  branch fuses, conductor and connector ratings from these measurements and limits.
- Calibrate anatomical indexes and sparse XY coordinates for each lamp separately.
  Exclude status; verify walking-pixel order before effects.
- Run both outputs with INMP441, all four buttons, local UI and authenticated WSS.
  Exercise native/audio/realtime effects, fast controls, body-off/status-on and
  status priority. Test mic channel/timing and false button holds under LED load.
- Test router/cloud loss and recovery without losing local controls. Record heap,
  reconnects, reset reason and command latency; reject queued/replayed/expired commands.
- Check cold/warm resets, intended power orders and supply droop/brownout recovery
  without enabling an unverified USB/external controller power combination.

## 4. Repeatable acceptance on both finished lamps

These are proposed project qualification targets, not manufacturer certification.
Use the intended protected current limit and assembled base/enclosure.

| Test | Target for each lamp | Acceptance |
|---|---|---|
| Cold starts | 30 independent starts, varied off intervals | Correct boot, no unintended pixel flashes, lost settings or persistent faults |
| Warm resets | 30 resets | Both outputs, local UI, mic and buttons recover correctly |
| Wi-Fi/cloud recovery | 20 controlled disconnect/reconnect cycles | Local controls remain usable; connection recovers; no stale command execution |
| Load/thermal run | 24 h: recorded static-load and dynamic/audio blocks | Zero observed data glitches/uncommanded resets; current/voltage/temperature within limits fixed before the test |
| Status isolation | At least30 repetitions across native/audio/realtime modes | Body effects never paint status; body off still permits bounded system status |
| Final harness | Both actual lamps, unchanged wiring/passive values | No visible flicker, corrupt colours, spurious resets or failed transitions |
| Recovery/onboarding | Both lamps; iPhone and Android, intended two-home setup | Correct private identity, QR/AP Wi-Fi setup, recovery, NFC readback and internet-outage local operation |

Set and record acceptable voltage, component/enclosure temperature and load limits
before the full-load run, using the actual parts and materials. Observe and log
throughout; a24 h elapsed timer alone does not establish glitch-free operation.
If a test changes the wire layout, passive values, PSU, firmware or pixel lot,
repeat affected qualification blocks on the final combination. Neither lamp ships
with a reproduced unexplained fault or an outstanding carrier/backfeed gate.
Other existing firmware/security release gates remain in [validation](../docs/validation.md).

## Evidence sheet — complete separately for each lamp

- Serial and actual pixel lot/driver identification; status/body counts.
- Board markings, pin/power-path evidence, permitted USB/service power arrangement.
- Firmware SHA256 and upstream version; measured timing/colour order and config.
- Data/ground lead length/routing; series and pulldown values or link/DNP.
- PSU settings, measured load, fuse/gauge/connector/injection details.
- GPIO/DIN high/low relative to pixel GND, waveforms, rail drop and ground offset.
- Every test's date, duration/cycle count, conditions, observations and pass/fail.
- Temperature/voltage limits, maxima/minima, reset/heap/reconnect observations.
- Phone/NFC/recovery results; operator and final shipment decision.

Keep private account/Wi-Fi/factory values out of shared evidence and the public repo.
For a fault, first reproduce it and save the capture and exact configuration.
Change one variable at a time. Report evidence and corrective options to the owner;
no automatic translator insertion and no repeated reopening based on speculation.
