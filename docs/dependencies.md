# Dependency disclosure

Backend direct dependencies are pinned in `requirements.txt`. Firmware build
tooling has a separate `requirements-firmware.txt`, so PlatformIO's local UI
does not determine server dependency versions. Software tests use Python3.12.

WLED16.0.1 is pinned to `29b389df1c1aaec6ff53aea742d17063b985906c`.
OddCurrent's usermod uses links2004 WebSockets2.6.1; its ESP32 code follows
`setCACert` and hostname verification when a nonempty factory CA is supplied.
An empty CA prevents the adapter starting; it cannot fall back to insecure TLS.
Framework selection is espressif326.13.0 / Arduino2.0.17 / IDF4.4.7, the
upstream-documented alternative that includes `WiFiClientSecure`.

On 2026-10-12 the backend requirements audit returned **no known vulnerabilities**.
This is a dated package-advisory result, not a complete penetration test or
container/firmware security assessment.

The pinned upstream WLED npm lockfile reported **four high-severity development
dependency findings**: `brace-expansion`, `braces`, `chokidar` and `nodemon`, involving
pattern-expansion denial of service. These tools build/watch WLED's web assets;
they are not dependencies of the OddCurrent hosted interface or Python service.
The development build consumes the pinned upstream source, not uploaded build
patterns. Do not run an automatic broad upstream dependency update as a substitute
for review. A shipping firmware needs upstream dependency review, an updated/pinned
build-tool override if appropriate, signature/recovery acceptance and renewed audit.

Licences: OddCurrent original source/assets MIT; WLED and its own files retain
upstream MIT/EUPL notices and third-party dependencies retain their respective
licences. Distribute the exact modified source and upstream revision beside any
firmware binary. CI artifacts are marked DEVELOPMENT ONLY and unsigned.
