# UI foundation

OddCurrent consumes [313 Command v1.1.0](https://github.com/sheldondickinson/313-command/tree/v1.1.0).
`design-system.lock.json` pins the source tag, manifest checksum and exact vendored
CSS hashes. Shared files remain byte-identical. No runtime hotlink or new framework
is used. The manifest/guide were read through the authenticated source connector;
private operational endpoints are not included in this public consumer.

The admin header, cards, badges, inputs, buttons, focus states and spacing use the
shared component/token contract. `command-adapter.css` maps existing lamp controls
onto that foundation. OddCurrent wordmarks, David illustration/editorial hero type,
and six lighting-effect swatches retain application identity and domain meaning.
The operator view uses shared typography, graphite surfaces, orange actions and
semantic health colours. The compact metric summary uses two noninteractive tiles
per row; device/detail content becomes one column on phones.

The existing lamp artwork proportions are editorial application extensions, not
new shared tokens. No shared package source or other consumer is changed. Upgrades
are deliberate changes to a new exact vendor directory and lockfile. Git retains
the prior consumer state for rollback. Automated hash/contract tests and browser
viewport checks accompany adoption; physical devices and screen readers require
separate attributed acceptance.
