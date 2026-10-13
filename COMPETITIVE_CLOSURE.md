# TasteTruce 2026 Competitive Closure — Evidence and Freeze

## Submission
Already submitted to Qloo Agentic Hackathon on Devpost, per the submit confirmation screenshot. Do **not** edit, withdraw, or replace the submitted entry during this closure.

## Baseline and improvements
- Authenticated Qloo from hosted Render verified earlier by user screenshot (LIVE_QLOO).
- Validated movie match in original screenshot: Children of Men.
- Dining landmark bug observed (Brooklyn Bridge) and category gate added; unverified places are excluded.
- Missing Qloo affinities are never replaced with invented numeric scores; a shared entity can be shown with source qloo_rank and Qloo result positions instead.
- Candidate pool expanded to 30 with unchanged number of Qloo calls in PR #10.
- PR #12 distinguishes empty eligible candidate sets from genuine cross-person disagreement.
- CI validates diverse offline fixtures including three participants, category filters, missing affinities and bounded Qloo calls.

## Reproducible validation
Run `python3 -m unittest discover -s . -p 'test_*.py' -v`.
GitHub Actions workflow: `.github/workflows/tests.yml`.

## Public demo
https://tastetruce-qloo-demo.onrender.com
Health endpoint: https://tastetruce-qloo-demo.onrender.com/healthz
Public repo: https://github.com/hgreco85/TasteTruce-Qloo

## Honest limitations
- Offline matrix is not the same as an authenticated live multi-profile validation.
- Hosted endpoint could not be independently inspected by the assistant's network environment during final closure.
- Need fresh screenshots of real post-PR #12 output for film/music/dining to claim visual validation. Earlier screenshot is evidence of an earlier release only.
- A strict dining filter may suppress restaurants lacking machine-readable food-service tags.
- Rate cap is process-local and not a durable distributed quota.

## Release policy
Only deploy changes passing GitHub CI; preserve prior Render version for rollback.
Freeze feature development after at most two cycles, except critical bugs. Recheck Render deployment live state and surface issues without modifying Devpost.
