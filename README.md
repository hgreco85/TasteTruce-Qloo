# TasteTruce

A fairness-first, Qloo-powered cultural recommendation agent for groups.

## Run

Python 3.10+; no third-party packages required.

```bash
python3 web.py
```

Visit http://127.0.0.1:8080. Default mode uses clearly labeled offline fixtures.

To use live Qloo recommendations, set `QLOO_API_KEY` as a server-side environment secret and run:

```bash
python3 web.py --live
```

Never put the Qloo key in browser code, Git or logs.

## Test

```bash
python3 -m unittest discover -s . -p 'test_*.py' -v
```

## How it works

Each person's tastes are resolved separately; Qloo suggestions are intersected across participants and scored with 70% weight on the weakest-person affinity and 30% on the average. No fabricated live recommendations.

Current limitations: artist-name input anchors, simple local UI, no hosted live demo yet.

MIT licensed. Built for [Qloo Agentic Hackathon](https://qloo.devpost.com/).