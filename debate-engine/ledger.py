class Ledger:
    """Shared evidence ledger. Every tool result gets an ID like E1, E2..."""

    def __init__(self):
        self.items = {}

    def add(self, agent: str, tool: str, args: dict, data: str) -> str:
        eid = f"E{len(self.items) + 1}"
        self.items[eid] = {"agent": agent, "tool": tool, "args": args, "data": data}
        return eid

    def compact(self, limit: int = 700) -> dict:
        """Shortened copy for the judge prompt."""
        return {
            k: {"agent": v["agent"], "tool": v["tool"], "args": v["args"], "data": v["data"][:limit]}
            for k, v in self.items.items()
        }
