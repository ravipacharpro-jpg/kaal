"""MCP registry stub — browser + github pre-configured, auto load/unload Phase-2."""
SERVERS = {"browser": {"cmd": "npx @playwright/mcp --headless", "on_demand": True},
           "github": {"cmd": "github-mcp", "on_demand": True}}
