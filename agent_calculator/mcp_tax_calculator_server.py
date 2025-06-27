#!/usr/bin/env python3
"""
MCP Tax Calculator Server
"""

from mcp.server.fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP("tax-calculator")

# Tax data
tax_data = {
    "federal_tax_rate": 0.22,
    "state_tax_rate": 0.05,
    "effective_tax_rate": 0.27,
    "tax_brackets": [
        {"min": 0, "max": 10000, "rate": 0.10},
        {"min": 10000, "max": 40000, "rate": 0.12},
        {"min": 40000, "max": 85000, "rate": 0.22},
        {"min": 85000, "max": 163300, "rate": 0.24},
        {"min": 163300, "max": 207350, "rate": 0.32},
        {"min": 207350, "max": 518400, "rate": 0.35},
        {"min": 518400, "max": None, "rate": 0.37}
    ],
    "deductions": {
        "standard_deduction": 12950,
        "itemized_deductions": {
            "mortgage_interest": 0,
            "property_tax": 0,
            "charitable_contributions": 0
        }
    },
    "credits": {
        "child_tax_credit": 2000,
        "earned_income_credit": 0
    }
}

@mcp.tool()
def calculate_tax() -> dict:
    """Calculate tax rates, brackets, deductions, and credits"""
    return {
        "message": "Tax calculations completed",
        "tax_result": tax_data
    }

@mcp.tool()
def get_tax_brackets() -> list:
    """Get current tax brackets"""
    return tax_data["tax_brackets"]

@mcp.tool()
def get_tax_rates() -> dict:
    """Get current tax rates"""
    return {
        "federal_tax_rate": tax_data["federal_tax_rate"],
        "state_tax_rate": tax_data["state_tax_rate"],
        "effective_tax_rate": tax_data["effective_tax_rate"]
    }

@mcp.tool()
def get_deductions() -> dict:
    """Get available deductions"""
    return tax_data["deductions"]

@mcp.tool()
def get_credits() -> dict:
    """Get available tax credits"""
    return tax_data["credits"]

if __name__ == "__main__":
    mcp.run() 