import asyncio
from typing import Dict, Any, List
from langchain_mcp_adapters.client import MultiServerMCPClient
from app.core.config import settings

MCP_TOOL_TIMEOUT = 30

def create_mcp_client(swiggy_access_token: str) -> MultiServerMCPClient:
    """
    Creates a MultiServerMCPClient instance connected to Swiggy Food MCP.
    Directly extracted from notebook Cell 18.
    """
    if not swiggy_access_token:
        raise RuntimeError("Swiggy access token is missing.")

    return MultiServerMCPClient(
        {
            "swiggy": {
                "transport": "streamable_http",
                "url": settings.SWIGGY_MCP_URL,
                "headers": {
                    "Authorization": f"Bearer {swiggy_access_token}"
                },
            }
        }
    )

async def get_mcp_tools(swiggy_access_token: str) -> List[Any]:
    """
    Retrieves available MCP tools from the Swiggy server.
    Directly extracted from notebook Cell 19.
    """
    client = create_mcp_client(swiggy_access_token)
    return await client.get_tools()

async def invoke_mcp(
    tool_name: str,
    arguments: Dict[str, Any],
    swiggy_access_token: str,
    timeout: int = MCP_TOOL_TIMEOUT
) -> Any:
    """
    Centralized safe Swiggy MCP invocation wrapper.
    Directly extracted from notebook Cell 21.
    """
    tools = await get_mcp_tools(swiggy_access_token)
    tool_map = {t.name: t for t in tools}

    if tool_name not in tool_map:
        raise RuntimeError(f"Swiggy MCP tool not available: {tool_name}")

    tool = tool_map[tool_name]

    try:
        return await asyncio.wait_for(
            tool.ainvoke(arguments),
            timeout=timeout
        )
    except asyncio.TimeoutError as e:
        raise TimeoutError(
            f"Swiggy MCP tool '{tool_name}' timed out after {timeout} seconds."
        ) from e
