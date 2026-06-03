import asyncio
import os
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv(override=True)

async def test_github_mcp():
    server_params = StdioServerParameters(
        command="npx.cmd",
        args=["-y", "@modelcontextprotocol/server-github"],
        env={**os.environ, "GITHUB_PERSONAL_ACCESS_TOKEN": os.getenv("GITHUB_PAT")}
    )

    owner = os.getenv("GITHUB_OWNER", "CS8867")
    repo = os.getenv("GITHUB_REPO", "ai-ops-sentinel")

    print(f"[1] Spawning MCP GitHub server via npx.cmd...")
    print(f"[2] Target: {owner}/{repo} branch=ai-remediation")

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("[3] MCP session initialized.")

            tools = await session.list_tools()
            print(f"[4] Available tools: {[t.name for t in tools.tools]}")

            print("[5] Pushing dummy file...")
            result = await session.call_tool("create_or_update_file", {
                "owner": owner,
                "repo": repo,
                "path": "mcp_test.md",
                "content": "# MCP test\nMCP GitHub integration is working.\n",
                "message": "test: verify MCP GitHub connection",
                "branch": "ai-remediation"
            })
            print(f"[6] Done. Result: {result}")

asyncio.run(test_github_mcp())
