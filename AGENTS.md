# OddCurrent repository guidance

UI work consumes [313 Command](https://github.com/sheldondickinson/313-command)
**v1.1.0**, pinned in `design-system.lock.json`. Read the upstream `AGENTS.md`,
manifest and relevant guides at that exact ref. Keep shared assets byte-identical;
use `--c313-*` and reusable components, with OddCurrent extensions under `--app-*`.
Preserve branding, effect colours, real permissions and device behaviour.

Firmware uses the exact upstream revision in `firmware/upstream.json`; read its
applicable repository guidance before changing hooks. Hardware release flags and
measured coordinates must never be invented to enable software features.
