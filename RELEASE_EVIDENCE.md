# TasteTruce — Competition evidence and release freeze (2026-10-13)

**Devpost:** Submitted (confirmed in organizer submission screenshot supplied by project owner). Do not remove or modify submission.

## Public artifacts
- Application: https://tastetruce-qloo-demo.onrender.com
- Public open-source repo: https://github.com/hgreco85/TasteTruce-Qloo
- Submission draft: [SUBMISSION_DRAFT.md](SUBMISSION_DRAFT.md)

## What has been observed
- Project owner supplied a browser screenshot showing `LIVE_QLOO`, a shared film recommendation, and a non-food landmark accidentally classified as dining.
- Dining validation was added and tested: known landmarks without food-service metadata are rejected.
- A later screenshot showed all categories without matches after introducing strict affinity validation. The scoring engine was corrected to retain actual shared Qloo entities even when no numeric affinity was supplied, showing their shared per-participant result positions rather than inventing scores.
- Offline deterministic tests now cover genuine shared matches, no-overlap cases, restaurant filtering, 2- and 3-person inputs, and the extended candidate window (30 candidates per insights call).

## Validation boundaries
GitHub CI verifies mocked API responses and program logic. These tests **do not prove** that arbitrary artists and places yield quality results from the live Qloo service. The earlier observed `LIVE_QLOO` browser screenshot confirms authenticated use for that particular query only. Reproduce a browser test after each code change before claiming a new set of recommendations.

## Release guardrails
- Keep the deployment on Render Free; avoid additional paid hosting.
- Never expose QLOO_API_KEY in public files, logs, client code or screenshots.
- Deploy only after CI succeeds; keep last-known-good commit/deploy for rollback.
- Do not invent matches or affinities when Qloo doesn't provide them.
- Do not change the already-submitted Devpost entry without explicit need.
- Treat live-mode request quotas as per-process safety limits, not distributed rate limiting.
- Review three representative profiles manually in the hosted demo before final freeze:
  1. Radiohead / Daft Punk
  2. Beyoncé / Coldplay
  3. Miles Davis / Taylor Swift
- For each case, check that the app says LIVE_QLOO, recommendations are real category matches, and rank-only evidence is not presented as affinity.

## Final status
Submitted project and public demo established. Last deployment must reach `live` and a final human/browser walkthrough must pass before marking the current commit frozen.
