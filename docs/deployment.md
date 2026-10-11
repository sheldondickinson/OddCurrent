# Deploy and recover

This portable runbook was exercised on the owner’s deployment on 12 October 2026.
Actual endpoints, workload roles and server paths remain in the private operating
registry. Use a dedicated app OIDC client with
exact HTTPS callback `<origin>/auth/callback`, issuer and signing-key discovery.
Enable code + PKCE S256 and give gift accounts access to this application only.
Validate allowed/denied accounts and claim replay in the real browser before
shipping. Browser sessions are opaque, HttpOnly, Secure and revocable; OIDC
temporary state uses a separate 10-minute signed cookie. No forwarded user-header
authentication is trusted. Configure a narrow workload identity in the existing
secret platform; do not reuse another application's grants.

1. Verify host storage/RAM capacity and existing ingress health. Capture the
   affected proxy configuration and available rollback route. No cleanup/pruning.
2. Create the protected mode-0600 runtime configuration from
   `server/runtime.example.json`, owned/readable by container UID10001. Inject it
   through the approved secret consumer; no credential environment variables.
3. Run `docker compose config --quiet`, build the image and record its digest.
   Use a single worker. Test the local health endpoint and authenticated routes.
4. Add only the new exact hostname to the existing server proxy/tunnel. WebSockets
   must pass `/ws/devices/*` with Authorization intact. Disable interactive access
   challenges on the device socket; per-device authentication remains mandatory.
   Impose 4 KiB HTTP body, WebSocket and sensible request/connection rate limits
   at the reverse proxy. Keep the origin port bound to loopback or a private
   isolated container network. Do not proxy the native WLED device APIs.
5. Set DNS and public HTTPS for the confirmed origin. Test certificate validation,
   OIDC login, an unrelated-account denial, device WSS, disconnect and reconnect.
6. Register each unique private factory bundle centrally, provision the physical
   MCU and verify acknowledgements/telemetry before activating electrical outputs.
7. Record service, opaque secret references, running digest and tests in the
   private documentation registry. Confirm canonical publication revision.

The Compose secret must be **mode 0600** and readable inside the container. Docker
Compose file secrets bind-mount native file permissions, so arrange UID10001
ownership; do not broaden permissions to work around deployment. The service
fails closed on missing/invalid production configuration.

## Health, update and rollback

`/healthz` checks the database and returns mode. Health alone is not OIDC, WSS or
hardware proof. Logs contain fixed event names rather than incoming raw payloads.
SQLite keeps up to 1000 events and 24-hour command receipts; pending commands
expire after 10 seconds and are never delivered after reconnection.

Use SQLite's online backup API (`scripts/backup.py`) into protected storage and
test restoration to a separate process/path. Preserve ownership, credentials,
sequences and invites. After restoring stale backups, revoke/reissue outstanding
sessions/invites and rotate affected credentials via a controlled overlap/cutover.
Store factory recovery material separately from the running server.

Backend rollback: preserve database backup, keep prior image digest and only
replace the OddCurrent container. This initial schema has no destructive migration.
Firmware update remains disabled in the cloud until a signed, allowlisted release
with board-specific compatibility, USB recovery and physical interruption tests is
accepted. Never treat a SHA-256 manifest as a cryptographic signature. WLED's own
native OTA remains a trusted-LAN development path; enable a strong private OTA
password before shipping. Secure boot and flash encryption are not enabled by
this source and no physical tamper protection is claimed.
