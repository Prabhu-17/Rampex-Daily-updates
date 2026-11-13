from mcp.server.fastmcp import FastMCP
from common import web_search

mcp = FastMCP("optimist")


@mcp.tool()
def find_strengths(topic: str) -> str:
    """Search the web for the strongest advantages and praised features of a product, stack or destination."""
    return web_search(f"{topic} advantages pros why choose best features")


@mcp.tool()
def find_success_stories(topic: str) -> str:
    """Search for positive real-world experiences: happy owners, successful projects, great trips."""
    return web_search(f"{topic} success story positive experience worth it review")


if __name__ == "__main__":
    mcp.run()
