# OddCurrent brand and experience guide

## Identity

Name: **OddCurrent**. Tagline: **Make the unexpected move.**

OddCurrent is the reusable hardware/software platform for eccentric connected inventions: animated sculptures, lamps, toys, installations and experimental devices. Collections may have their own names (e.g., **Lumen Oddities** for sculptural lighting), but the core device fleet, app and software remain OddCurrent. Product: **David / Edition 001**.

Visual personality: experimental maker studio meets a well-crafted object. Confident and playful, not neon-gamer or generic home automation. Logo icon combines an open orbital circuit with a spark/node, hinting at both motion and light. Use it for PCB silkscreen, sticker, screen, favicon and GitHub.

| Role | Hex |
|---|---|
| Night / main background | `#0B1220` |
| Deep card | `#162131` |
| Dividers/slate | `#29384B` |
| Warm paper / foreground | `#F4F0E8` |
| Muted foreground | `#B9C5D2` |
| Electric coral / primary accent | `#FF805A` |
| Signal cyan | `#5BC8E8` |
| Motion pistachio | `#B6E37A` |
| Error red | `#E45F68` |

Use a modern grotesk/system font for controls; a carefully chosen expressive display typeface for brand headings. Text contrast must be checked for WCAG AA. **Not every status light colour is a UI status colour**: semantic online/offline colours and the anatomical LED patterns are independent. Avoid colour-only meaning.

## Owner UI structure

- Top: OddCurrent logo, product name David, Live/offline chip, overflow/help.
- Hero: David product silhouette/owner-uploaded photo, subtle ambient vignette based on selected scene.
- Primary controls: on/off, intuitive brightness control, six scene tiles: Gallery White, Sunset, Electric Blue, Spectrum, Pulse, Music.
- Advanced collapsibles: anatomy/zone map, music-reactive levels, scene editor, schedules, status light intensity, WLED local link when on same network.
- Owner settings: network instructions, firmware info, updates, invite guest, recovery, diagnostics.
- Admin dashboard: dual-device list with last check-in, logs redacted, release controls. Must not display raw credentials.

## SVG asset inventory

`assets/logo-horizontal.svg`, `assets/logo-mark.svg`, `assets/logo-light.svg`, `assets/favicon.svg`; these are editable SVG concept art and can be refined in Figma/Inkscape. See mockup for CSS design starting point.
