import asyncio
from contextlib import AsyncExitStack

from agents import Agent, AGENT_SPECS
from ledger import Ledger
from judge import judge_verdict


async def run_debate(question: str, emit):
    ledger, transcript = Ledger(), []
    await emit({"type": "start", "question": question,
                "agents": [{"name": s["name"], "emoji": s["emoji"], "color": s["color"]}
                           for s in AGENT_SPECS]})

    async with AsyncExitStack() as stack:
        agents = [Agent(s) for s in AGENT_SPECS]
        # Connect one at a time: MCP stdio clients use anyio task groups, which must be
        # entered and exited from the same task (asyncio.gather would break that).
        for a in agents:
            await a.connect(stack)

        async def round_(n, label, make_prompt, use_tools=True):
            await emit({"type": "round", "n": n, "label": label})
            texts = await asyncio.gather(*(
                a.speak(make_prompt(a), ledger, emit, use_tools) for a in agents))
            for a, t in zip(agents, texts):
                transcript.append((n, a.name, t))
                await emit({"type": "say", "agent": a.name, "text": t, "round": n})

        def digest(rounds):
            return "\n\n".join(f"{n}: {t}" for r, n, t in transcript if r in rounds)

        # Round 1: opening statements (parallel)
        await round_(1, "Opening statements",
                     lambda a: f"Decision: {question}\n\nGive your opening position.")

        # Round 2: rebuttal. Everyone sees all openings.
        await round_(2, "Rebuttal",
                     lambda a: (f"Decision: {question}\n\nOpening statements:\n{digest({1})}\n\n"
                                "Rebut the strongest opposing point with evidence. "
                                "You may call your tools again."))

        # Round 3: final stance, no tools, short
        await round_(3, "Final stance",
                     lambda a: (f"Decision: {question}\n\nDebate so far:\n{digest({1, 2})}\n\n"
                                "Final stance in under 60 words: name the option you recommend and "
                                "the one thing that would change your mind. No new tool calls."),
                     use_tools=False)

        await emit({"type": "round", "n": 4, "label": "Judge deliberating"})
        verdict = await judge_verdict(question, transcript, ledger)
        await emit({"type": "verdict", "data": verdict, "evidence": ledger.items})
    await emit({"type": "done"})
    return verdict
