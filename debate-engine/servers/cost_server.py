"""Cost analyst tools. Pure math, no network. Currency-agnostic (works for INR, USD...)."""
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("cost")


@mcp.tool()
def total_cost_of_ownership(price: float, years: int, resale_pct: float = 0.3,
                            yearly_running_cost: float = 0.0) -> dict:
    """Total cost of ownership. resale_pct is the fraction of price recovered at the end (0.3 = 30%)."""
    years = max(years, 1)
    resale = price * resale_pct
    tco = price + yearly_running_cost * years - resale
    return {"tco": round(tco, 2), "per_year": round(tco / years, 2),
            "per_month": round(tco / (years * 12), 2), "assumed_resale": round(resale, 2),
            "years": years}


@mcp.tool()
def compare_prices(a: float, b: float) -> dict:
    """Absolute and percent difference between option A's price and option B's price."""
    return {"difference_b_minus_a": round(b - a, 2),
            "pct_b_vs_a": round((b - a) / a * 100, 1) if a else None}


@mcp.tool()
def monthly_emi(price: float, annual_rate_pct: float, months: int) -> dict:
    """EMI / instalment calculation for financing a purchase."""
    months = max(months, 1)
    r = annual_rate_pct / 12 / 100
    emi = price / months if r == 0 else price * r * (1 + r) ** months / ((1 + r) ** months - 1)
    total = emi * months
    return {"emi": round(emi, 2), "total_paid": round(total, 2),
            "interest_paid": round(total - price, 2)}


@mcp.tool()
def cost_per_use(price: float, uses_per_year: float, years: int) -> dict:
    """Cost per use (per day of use, per trip day, per work session...)."""
    total_uses = max(uses_per_year * years, 1)
    return {"cost_per_use": round(price / total_uses, 2), "total_uses": total_uses}


if __name__ == "__main__":
    mcp.run()
