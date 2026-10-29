# TasteTruce deployment readiness — DRAFT ONLY

No deployment or Devpost changes have been authorized.

## Preconditions
1. Verify the **authenticated** Devpost submission and record the exact `Try it out` value.
2. Confirm hosting free-tier availability, zero payment method requirement and no automatic billable upgrades. Do not create/bind infrastructure without explicit authorization.
3. Review the `render.yaml` blueprint and verify Render's currently supported configuration syntax before using it.
4. Ensure `QLOO_API_KEY` is held only as a server-side secret, never committed or sent in client assets. Without it the app runs **OFFLINE_FIXTURE**, not live Qloo.
5. Observe `QLOO_MAX_LIVE_REQUESTS` and external API request limits. Free hosting availability is not guaranteed.

## Once separately authorized
- Create a fresh app with this repo/branch and no automatic deploy, no billing, then choose deployment parameters explicitly.
- Check `GET /`, `HEAD /`, `GET /healthz` and POST `/api/plan` using two artists and a city, from a private browsing session.
- Verify response `mode` is **LIVE_QLOO** for real results; **OFFLINE_FIXTURE** cannot be represented as live results.
- Search response HTML/JS and network requests for `QLOO_API_KEY` and actual secret values; do not include those values in logs.
- Confirm that Devpost project, repo and demo all refer to TasteTruce; then request explicit authorization **before** editing `Try it out` or resubmitting.
- Rollback: unpublish/delete the deployed service after separate approval if necessary. Never use Railway.

## Current evidence
- Public repo and MIT LICENSE verified via GitHub.
- Main README: 'no hosted live demo yet'.
- Public Devpost project: https://devpost.com/software/tastetruce-find-common-ground
- Public project request returned HTTP 403 in audit browser; actual submitted 'Try it out' unknown.
- Official rules: https://qloo.devpost.com/
- Deadline: 30 Oct 2026 23:45 EDT (31 Oct 00:45 ART).
