import re
import json
from openai import AsyncOpenAI

import config
from agents import client

SYSTEM = """You are an impartial judge of a decision debate between four agents:
Optimist, Skeptic, Cost Analyst, Risk Analyst. You get the transcript and an evidence
ledger (IDs like E1, E2 produced by the agents' tools).

Return ONLY a JSON object, no markdown, with exactly these keys:
{
  "decision": "the concrete recommendation, one or two sentences",
  "confidence": integer 0-100,
  "scores": {"Optimist": 0-10, "Skeptic": 0-10, "Cost Analyst": 0-10, "Risk Analyst": 0-10},
  "key_evidence": [{"id": "E3", "why": "one sentence on why this evidence mattered"}],
  "deciding_factor": "the single thing that tipped the decision",
  "what_would_change_my_mind": "specific evidence or condition that would flip the verdict"
}
Scores rate how well each agent argued (use of evidence, accuracy, relevance).
Only cite evidence IDs that exist in the ledger. Pick 3-6 key_evidence items.
Lower your confidence when evidence is thin or assumptions were guessed."""

AGENT_NAMES = ["Optimist", "Skeptic", "Cost Analyst", "Risk Analyst"]


def _extract_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object found")
    return json.loads(text[start:end + 1])


def _clean(v: dict, ledger) -> dict:
    """Validate and repair the judge's output. Drops hallucinated evidence IDs."""
    out = {
        "decision": str(v.get("decision", "No decision returned")),
        "deciding_factor": str(v.get("deciding_factor", "")),
        "what_would_change_my_mind": str(v.get("what_would_change_my_mind", "")),
    }
    try:
        out["confidence"] = max(0, min(100, int(v.get("confidence", 50))))
    except (TypeError, ValueError):
        out["confidence"] = 50
    scores = v.get("scores", {}) or {}
    out["scores"] = {}
    for n in AGENT_NAMES:
        try:
            out["scores"][n] = max(0, min(10, float(scores.get(n, 5))))
        except (TypeError, ValueError):
            out["scores"][n] = 5
    out["key_evidence"] = []
    for item in v.get("key_evidence", []) or []:
        eid = str(item.get("id", "")).strip().strip("[]")
        if eid in ledger.items:
            out["key_evidence"].append({"id": eid, "why": str(item.get("why", ""))})
    return out


async def judge_verdict(question: str, transcript: list, ledger) -> dict:
    debate = "\n\n".join(f"[Round {r}] {n}: {t}" for r, n, t in transcript)
    user = (f"Decision question: {question}\n\nDEBATE:\n{debate}\n\n"
            f"EVIDENCE LEDGER:\n{json.dumps(ledger.compact(), ensure_ascii=False)}")
    last_err = None
    for attempt in range(3):
        try:
            kwargs = dict(model=config.JUDGE_MODEL, max_tokens=1500, temperature=0.2,
                          messages=[{"role": "system", "content": SYSTEM},
                                    {"role": "user", "content": user}])
            if attempt == 0:
                kwargs["response_format"] = {"type": "json_object"}
            resp = await client.chat.completions.create(**kwargs)
            return _clean(_extract_json(resp.choices[0].message.content or ""), ledger)
        except Exception as e:  # bad JSON, model without json mode, transient API error
            last_err = e
    return {"decision": f"Judge failed: {last_err}", "confidence": 0,
            "scores": {n: 0 for n in AGENT_NAMES}, "key_evidence": [],
            "deciding_factor": "", "what_would_change_my_mind": ""}
