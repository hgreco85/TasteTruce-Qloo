# Devpost submission draft — TasteTruce (NOT SUBMITTED)

## Project title
TasteTruce — A Fairness-First Cultural Negotiation Agent

## Elevator pitch
Different tastes, one shared experience. TasteTruce uses Qloo's Taste AI to negotiate personalized cultural experiences across people without leaving anyone behind.

## Inspiration
Most recommendation systems optimize an average. But a group's great choice needs to work for the least enthusiastic person, too. TasteTruce treats taste alignment as negotiation, not popularity.

## What it does
Enter each participant's favorite artist. The resolver discovers Qloo entities, runs separate cross-domain Qloo insights calls for each person, intersects verified suggestions, and ranks common items using a fairness-first score (70% weakest-member affinity, 30% mean). It can recommend across movies, music, dining, and books where supported. If no shared evidence is returned, it says so rather than inventing a match.

## How we built it
Python 3 standard library; server-side authenticated calls to Qloo search and insights; deterministic candidate intersection and rank aggregation; responsive accessible HTML/CSS/JavaScript; unit and workflow tests on GitHub. Server-side credentials, no secret in client or source.

## Challenges
Reliable entity resolution, cross-domain compatibility, truthful recommendation evidence and keeping an API-backed web demo secure and low cost.

## Accomplishments
Real two-person Qloo smoke test completed successfully: both artist names resolved; shared movie candidate found; music had no overlapping candidate in the returned results. Public standalone MIT-licensed code with CI and Render-hosted demonstration.

## Learned
A credible agent should acknowledge missing evidence and balance user utility across every group member instead of manufacturing a winning recommendation.

## What's next
Improve entity-type detection, category-specific input and rich explanations; add bounded quota protections and stronger request-validation; verify the hosted live integration after adding the secret in Render; enhance visual design and share actual taste evidence.

## Technology
Qloo Taste AI API, Python, JavaScript, HTML, CSS, GitHub Actions, Render.

## Repository
https://github.com/hgreco85/TasteTruce-Qloo

## Demo (verify accessibility before submission)
https://tastetruce-qloo-demo.onrender.com

## Testing instructions
Open the demo, enter two artist names, click Find common ground. Any mode labeled OFFLINE_FIXTURE is **not** a real Qloo result. For a live Qloo-backed demo, server must be configured with QLOO_API_KEY and started with --live. The deployed environment is initially fixture-only; do not claim hosted live API until verified.

## Submission checklist
- [x] Public MIT source repository
- [x] Qloo live API tested in private CI
- [ ] Hosted demo confirmed reachable
- [ ] Hosted real API enabled and validated safely
- [ ] Final UI/functionality checked on phone and desktop
- [ ] Devpost submission created and confirmed
- [ ] License shows in GitHub About
