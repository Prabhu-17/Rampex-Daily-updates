from mcp.server.fastmcp import FastMCP
from common import web_search

mcp = FastMCP("skeptic")


@mcp.tool()
def find_complaints(topic: str) -> str:
    """Search for common complaints, drawbacks and negative reviews of a product, stack or destination."""
    return web_search(f"{topic} problems complaints drawbacks cons issues")


@mcp.tool()
def find_failure_reports(topic: str) -> str:
    """Search for failure stories, regrets, defects, outages or bad experiences."""
    return web_search(f"{topic} failed regret disappointed reliability problems reddit")


if __name__ == "__main__":
    mcp.run()
