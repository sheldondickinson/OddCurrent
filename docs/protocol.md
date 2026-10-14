# OddCurrent protocol 1

The device opens `wss://<confirmed-origin>/ws/devices/<serial>` with its unique
Bearer credential in the Authorization header. No query tokens or browser Origin
are accepted. Server hashes are compared in constant time. Public-root CA and
hostname verification are mandatory; firmware never calls `setInsecure`.
SNTP time must be valid before connecting. The server time within validated TLS
anchors command expiry. The socket's hello has protocol, random session nonce,
time and 15-second heartbeat interval. Session nonce changes each connection.

```json
{"type":"command","id":"00000000000000000000000000000001","seq":12,
 "expires":1700000010,"session":"00000000000000000000000000000002",
 "capability":"lighting","payload":{"on":true,"brightness":40,"scene":"sunset"}}
```

Sequences persist centrally. Device compares increasing sequence within the
current authenticated session and rejects expired/future-dated commands and all
inputs while updating. `ack` echoes ID/sequence with `applied` or `rejected`.
The API reports pending until acknowledgement; desired state does not prove the
lamp changed. Only strict authenticated telemetry supplies reported state.
Commands expire in 10 seconds. Connection loss marks pending receipts disconnected.
No delivery queue is drained on reconnect. Local effects/buttons continue offline.

`lighting` permits on, brightness 1–100, six curated scene keys, music,
sensitivity 1–100, status brightness 1–20 and a calibrated anatomical zone.
Zone changes permit on/brightness/scene only. Guests permit on/brightness/scene/
music only. No passthrough WLED JSON, arbitrary URLs, GPIO writes, motors or
remote factory/Wi-Fi reset or provisioning exist in this contract. Status pixels are outside zones.

Telemetry permits light state, RSSI, firmware ID, boot reason, reconnect count,
uptime and calibration readiness. Unknown fields (including microphone samples,
SSID/password or credentials) close the connection. Frame limit is 2048 bytes.
Firmware reconnects with exponential backoff and jitter, bounded at 60 seconds.
Rotate/revoke device credentials through a future reviewed administrative path;
this development version supports hash registration and manual controlled cutover,
not zero-downtime automated device credential rotation.

Administrator-only `maintenance` commands permit `refresh`, `identify`, `reboot`
and `locate_pixel` with a bounded body-local index. The same session, expiry,
sequence, update lockout and acknowledgement rules apply. Identify and locate
are temporary output overlays; they restore normal rendering automatically.
Restart is delayed long enough to send its acknowledgement. Neither action
changes Wi-Fi, factory identity, current caps or hardware acceptance.

Firmware0.3 adds typed optional diagnostics: localIPv4, free heap/PSRAM, error,
pixel counts, status display, management protocol and real AudioReactive numeric
level/window peak. No waveform/FFT/audio sample buffers are transmitted. LocalIP
is returned only to an explicitly authorised admin. Deploy the compatible backend
before this firmware because the telemetry schema rejects unknown fields.
