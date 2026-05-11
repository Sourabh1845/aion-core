"""Tiny stdio MCP-like server for AION firewall demos.

This is not a production MCP server. It is only here so the firewall can be
demoed with one command and no external dependencies.
"""

from __future__ import annotations

import json
import sys


def main() -> int:
    for line in sys.stdin:
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue

        method = request.get("method")
        if method == "initialize":
            respond(request, {"server": "aion-demo-mcp", "version": "0.1.0"})
        elif method == "tools/list":
            respond(
                request,
                {
                    "tools": [
                        {"name": "shell", "description": "Demo shell command tool."},
                        {"name": "read_file", "description": "Demo file read tool."},
                    ]
                },
            )
        elif method == "tools/call":
            params = request.get("params") or {}
            respond(
                request,
                {
                    "content": [
                        {
                            "type": "text",
                            "text": f"demo tool executed: {params.get('name')}",
                        }
                    ]
                },
            )
        else:
            error(request, -32601, "Method not found")
    return 0


def respond(request: dict, result: dict) -> None:
    print(
        json.dumps(
            {"jsonrpc": "2.0", "id": request.get("id"), "result": result},
            separators=(",", ":"),
        ),
        flush=True,
    )


def error(request: dict, code: int, message: str) -> None:
    print(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {"code": code, "message": message},
            },
            separators=(",", ":"),
        ),
        flush=True,
    )


if __name__ == "__main__":
    raise SystemExit(main())
