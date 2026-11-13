# Multi-Agent Debate and Decision Engine (OpenRouter)

Four agents (Optimist, Skeptic, Cost Analyst, Risk Analyst) each connect to their **own MCP tool server**,
debate a decision over 3 rounds, and a **judge** returns a JSON verdict that cites evidence IDs from a shared
**evidence ledger**. A FastAPI + SSE backend streams everything to a live browser UI.

```
Orchestrator: Opening -> Rebuttal -> Final stance -> Judge
   Optimist     Skeptic     Cost Analyst    Risk Analyst
   (web search) (web search) (pure math)    (scoring + search)
        \           |            |            /
              Evidence Ledger (E1, E2, ...)
                        |
                      Judge -> verdict JSON -> UI
```

## Setup

```bash
cd debate-engine
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # Windows: copy .env.example .env
# edit .env and paste your OpenRouter key
```

## Run

Browser UI:
```bash
uvicorn app:app --reload
# open http://localhost:8000
```

Terminal only (good for first test):
```bash
python run_cli.py "Next.js vs Django for a startup MVP"
```

## Configure

All in `.env`:

| Variable | Purpose |
|---|---|
| `OPENROUTER_API_KEY` | your key |
| `DEBATER_MODEL` | fast model for the 4 debaters (must support tool calling) |
| `JUDGE_MODEL` | stronger model for the verdict |
| `TAVILY_API_KEY` | optional, better search. Without it DuckDuckGo is used |

Model slugs come from https://openrouter.ai/models. Filter by "tools" support. If an agent never calls
tools, your chosen model probably doesn't support them.

## File map

| File | Role |
|---|---|
| `servers/*.py` | the four MCP tool servers (`common.py` is the shared search helper) |
| `agents.py` | agent personas + the OpenRouter tool-calling loop over MCP |
| `ledger.py` | evidence IDs |
| `judge.py` | verdict prompt, JSON parsing, evidence-ID validation |
| `orchestrator.py` | the debate rounds |
| `app.py` | FastAPI + Server-Sent Events |
| `static/index.html` | the visual UI |
| `run_cli.py` | terminal runner |

## Troubleshooting

- **401 / "No auth"**: key missing or wrong. Check `.env`, restart uvicorn.
- **Agents answer without using tools**: model lacks tool support. Change `DEBATER_MODEL`.
- **Empty evidence / "backend: none"**: search failed. Add `TAVILY_API_KEY` or `pip install -U ddgs`.
- **Judge returns "Judge failed"**: try a stronger `JUDGE_MODEL`.
- **Slow**: each round is parallel, but 4 agents x several tool calls still takes ~30-90 s.

## Ideas to extend

- Moderator agent that picks the next speaker
- Human-in-the-loop constraint injection between rounds ("budget is 80k")
- SQLite persistence and replay
- Tool packs per decision type (flights/weather API for trips, price API for laptops)
