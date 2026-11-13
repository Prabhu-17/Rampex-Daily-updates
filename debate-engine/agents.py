import os
import sys
import json
import asyncio

from openai import AsyncOpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import config

BASE = os.path.dirname(os.path.abspath(__file__))

client = AsyncOpenAI(
    base_url=config.BASE_URL,
    api_key=config.API_KEY or "missing",
    default_headers={"HTTP-Referer": config.APP_URL, "X-Title": config.APP_NAME},
)

RULES = (
    "Rules: use your tools to gather evidence before making claims. "
    "Cite evidence by its ID in square brackets, like [E3], right after the claim it supports. "
    "Never invent an ID. If a tool returned nothing useful, say so. "
    "Never concede unless evidence contradicts you. Keep every answer under 150 words, no preamble."
)

AGENT_SPECS = [
    {
        "name": "Optimist", "emoji": "🌞", "color": "#f5b942",
        "server": "optimist_server.py",
        "persona": ("You are the OPTIMIST in a decision debate. Make the strongest evidence-backed "
                    "positive case for the most promising option(s). Be specific, not cheerleading. " + RULES),
    },
    {
        "name": "Skeptic", "emoji": "🧐", "color": "#ef6b6b",
        "server": "skeptic_server.py",
        "persona": ("You are the SKEPTIC in a decision debate. Find real complaints, failures and hidden "
                    "downsides of the leading option(s). Attack weak or unsupported claims from others. " + RULES),
    },
    {
        "name": "Cost Analyst", "emoji": "💰", "color": "#4cc38a",
        "server": "cost_server.py",
        "persona": ("You are the COST ANALYST. You only care about money: total cost of ownership, value per "
                    "year, financing, cost per use. Always compute numbers with your tools (state your "
                    "assumptions, e.g. price, years, resale). If the user gave no prices, make clearly "
                    "labelled assumptions. " + RULES),
    },
    {
        "name": "Risk Analyst", "emoji": "🛡️", "color": "#6ea8fe",
        "server": "risk_server.py",
        "persona": ("You are the RISK ANALYST. Assess what could go wrong and how badly: reliability, "
                    "warranty, regret, reversibility. Use score_risk for each option and search for "
                    "warranty/reliability evidence. " + RULES),
    },
]


class Agent:
    def __init__(self, spec: dict, model: str = None):
        self.name = spec["name"]
        self.persona = spec["persona"]
        self.server_path = os.path.join(BASE, "servers", spec["server"])
        self.model = model or config.DEBATER_MODEL
        self.tools = []
        self.session = None

    async def connect(self, stack):
        params = StdioServerParameters(
            command=sys.executable, args=[self.server_path],
            env={**os.environ},  # pass TAVILY_API_KEY etc. to the tool server
        )
        r, w = await stack.enter_async_context(stdio_client(params))
        self.session = await stack.enter_async_context(ClientSession(r, w))
        await self.session.initialize()
        listed = await self.session.list_tools()
        self.tools = [{
            "type": "function",
            "function": {"name": t.name, "description": t.description or "",
                         "parameters": t.inputSchema},
        } for t in listed.tools]

    async def _chat(self, **kwargs):
        for attempt in range(3):
            try:
                return await client.chat.completions.create(**kwargs)
            except Exception:
                if attempt == 2:
                    raise
                await asyncio.sleep(1.5 * (attempt + 1))

    async def speak(self, prompt: str, ledger, emit, use_tools: bool = True) -> str:
        messages = [{"role": "system", "content": self.persona},
                    {"role": "user", "content": prompt}]
        for step in range(config.MAX_TOOL_STEPS + 1):
            tools_on = use_tools and self.tools and step < config.MAX_TOOL_STEPS
            kwargs = dict(model=self.model, messages=messages,
                          max_tokens=config.MAX_TURN_TOKENS, temperature=0.7)
            if tools_on:
                kwargs["tools"] = self.tools
                kwargs["tool_choice"] = "auto"
            resp = await self._chat(**kwargs)
            msg = resp.choices[0].message

            if not msg.tool_calls:
                return (msg.content or "").strip() or "(no response)"

            messages.append({
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [{"id": tc.id, "type": "function",
                                "function": {"name": tc.function.name,
                                             "arguments": tc.function.arguments or "{}"}}
                               for tc in msg.tool_calls],
            })
            for tc in msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                try:
                    out = await self.session.call_tool(tc.function.name, args)
                    payload = "".join(c.text for c in out.content if getattr(c, "type", "") == "text")
                    if out.isError:
                        payload = f"TOOL ERROR: {payload}"
                except Exception as e:
                    payload = f"TOOL ERROR: {e}"
                payload = payload[:config.MAX_TOOL_PAYLOAD]
                eid = ledger.add(self.name, tc.function.name, args, payload)
                await emit({"type": "tool", "agent": self.name, "tool": tc.function.name,
                            "args": args, "id": eid})
                await emit({"type": "evidence", "id": eid, "agent": self.name,
                            "tool": tc.function.name, "args": args, "data": payload})
                messages.append({"role": "tool", "tool_call_id": tc.id,
                                 "content": f"[{eid}] {payload}"})
        return "(no response)"
