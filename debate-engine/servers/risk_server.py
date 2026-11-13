from mcp.server.fastmcp import FastMCP
from common import web_search

mcp = FastMCP("risk")


@mcp.tool()
def score_risk(reliability_concern: int, reversibility_difficulty: int,
               cost_of_failure: int, uncertainty: int) -> dict:
    """Weighted risk score. Each input is 1 (low) to 10 (high):
    reliability_concern = how likely it breaks / disappoints,
    reversibility_difficulty = how hard it is to undo or resell,
    cost_of_failure = how bad it is if it goes wrong,
    uncertainty = how little reliable information exists."""
    c = lambda x: max(1, min(10, int(x)))
    r, v, f, u = c(reliability_concern), c(reversibility_difficulty), c(cost_of_failure), c(uncertainty)
    score = round(r * 0.35 + v * 0.20 + f * 0.30 + u * 0.15, 2)
    level = "low" if score < 4 else "moderate" if score < 7 else "high"
    return {"risk_score_out_of_10": score, "level": level,
            "inputs": {"reliability_concern": r, "reversibility_difficulty": v,
                       "cost_of_failure": f, "uncertainty": u}}


@mcp.tool()
def warranty_lookup(product: str) -> str:
    """Search the web for warranty, service-centre coverage and repair policy of a product."""
    return web_search(f"{product} warranty coverage service centre repair policy")


@mcp.tool()
def reliability_reports(topic: str) -> str:
    """Search for reliability data, failure rates, long-term ownership reports."""
    return web_search(f"{topic} long term reliability failure rate after 1 year")


if __name__ == "__main__":
    mcp.run()
