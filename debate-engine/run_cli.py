"""Run a debate in the terminal (no browser needed):
    python run_cli.py "MacBook Air M4 vs ThinkPad X1 Carbon for coding, budget 1.2 lakh INR"
"""
import sys
import json
import asyncio

import config
from orchestrator import run_debate


async def emit(e):
    t = e["type"]
    if t == "round":
        print(f"\n=== Round {e['n']}: {e['label']} ===")
    elif t == "tool":
        print(f"  🔧 {e['agent']} -> {e['tool']}({json.dumps(e['args'])})  [{e['id']}]")
    elif t == "say":
        print(f"\n{e['agent']}:\n{e['text']}")
    elif t == "verdict":
        print("\n=== VERDICT ===")
        print(json.dumps(e["data"], indent=2, ensure_ascii=False))
    elif t == "error":
        print("ERROR:", e["message"])


if __name__ == "__main__":
    if not config.API_KEY:
        sys.exit("Set OPENROUTER_API_KEY in .env first.")
    q = " ".join(sys.argv[1:]) or "MacBook Air M4 vs ThinkPad X1 Carbon for coding"
    asyncio.run(run_debate(q, emit))
