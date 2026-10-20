"""Read-only, synthetic invoice tool for the Curie live interview."""

from mcp.server import MCPServer


mcp = MCPServer("mock-invoices")


@mcp.tool()
def list_open_invoices() -> dict:
    """Return the current open invoices from a mock accounting system."""
    return {
        "invoices": [
            {
                "id": "INV-101",
                "customer": "Acme",
                "balance_cents": 120000,
                "due_date": "2026-09-19",
                "status": "open",
            },
            {
                "id": "INV-102",
                "customer": "Beta",
                "balance_cents": 80000,
                "due_date": "2026-09-18",
                "status": "open",
            },
            {
                "id": "INV-103",
                "customer": "Coda",
                "balance_cents": 50000,
                "due_date": "2026-10-25",
                "status": "open",
            },
            {
                "id": "INV-104",
                "customer": "Delta",
                "balance_cents": 25000,
                "due_date": None,
                "status": "open",
            },
        ]
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
