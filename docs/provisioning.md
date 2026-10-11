# Manufacturing and gift onboarding

Do not mint shipping identities until the real HTTPS origin, broker and public CA
chain are confirmed. `factory.py` creates unique random AP passwords, device
credentials and one-time ownership codes in a **new mode-0700 private directory**;
all outputs including the QR are mode 0600. Never place them in the public repo.

```sh
python scripts/factory.py david-001 --origin https://lamp.example.invalid \
  --broker-host lamp.example.invalid --ca /private/path/public-ca.pem \
  --out factory-private/david-001
python scripts/register_device.py --factory factory-private/david-001/factory.json \
  --database /private/path/oddcurrent.sqlite
```

Repeat with `david-002`; do not reuse a bundle or credential. Serial tooling must
read a private file, never accept credentials as arguments. Bundle re-creation
refuses to overwrite. Preserve factory identity when clearing home Wi-Fi.

NFC contains **only the public HTTPS device URL**. A private ownership insert goes
inside the base and is redeemed after account sign-in. URLs alone do not confer
ownership. Owner-created invitations explicitly grant time-limited curated guest
control and can be revoked. Register dedicated gift accounts restricted to this
application, not the operator's other applications.

The base label provides the AP Wi-Fi QR, serial and `http://4.3.2.1` fallback.
WPA2 protects the setup AP; the local captive portal is HTTP within that physical
setup boundary. Never promise end-to-end HTTPS over the captive portal. Keep the
AP password private enough to avoid an attacker nearby altering Wi-Fi. Disable
the AP after a successful association and retain access only via the recessed
recovery button / failed Wi-Fi boot. Home Wi-Fi credentials stay on the MCU.

## Recipient flow

1. Power on. Scan the base Wi-Fi QR and join the unique setup network.
2. Open the captive portal or `http://4.3.2.1`. Select home SSID and enter password.
3. Observe green confirmation and check the native local page if the internet is
   unavailable. Each lamp has its own `<serial>.local`; mDNS can fail on isolated
   Wi-Fi/subnets, so document finding its DHCP address.
4. Tap NFC for cloud control. Sign in and enter the private claim code once.
5. Hold recessed setup about 5 seconds to reopen setup without erasing; a deliberate
   15-second hold clears only Wi-Fi after visible warning. Factory identity remains.

## Required phone/bench acceptance

Test actual iPhone and Android QR joining, portal launch/fallback, wrong password,
hidden SSID, no internet, home Wi-Fi change, two devices on one LAN, NFC landing,
claim replay denial and unrelated account denial. NFC does not auto-join Wi-Fi on
iOS. A generated QR is not phone-tested onboarding. Before shipment verify HTTPS
destinations, encode/read back both NFC tags, then lock tags only after readback.
Keep one spare label/tag and a private revocation/recovery record.
