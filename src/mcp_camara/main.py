import json
import re
from collections.abc import Callable
from typing import Any

import httpx
import mcp.server.stdio
import mcp.types as types
from loguru import logger
from mcp.server.lowlevel import NotificationOptions, Server
from mcp.server.models import InitializationOptions

from mcp_camara.parser import load_openapi_spec, get_endpoints
from mcp_camara.tools import create_tools


BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"
SPEC_URL = f"{BASE_URL}/api-docs"

spec = load_openapi_spec(SPEC_URL)

endpoints = get_endpoints(spec)

tools = {tool.name: tool for tool in create_tools(endpoints)}

server = Server(name="mcp-camara", version="0.1.0")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return list(tools.values())


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
    tool = tools.get(name)

    if tool is None:
        logger.warning(f"Called unknown tool `{name}`.")
        return [types.TextContent(type="text", text=f"Called unknown tool `{name}`")]

    method_map: dict[str, Callable[..., httpx.Response]] = {
        "GET": httpx.get,
        "POST": httpx.post,
        "PUT": httpx.put,
        "PATCH": httpx.patch,
        "DELETE": httpx.delete
    }

    try:
        request_method = method_map[tool.meta["method"]]

        path: str = tool.meta["path"]

        for path_param in re.findall(r"\{([^}]+)\}", path):
            if param_value := arguments.get(path_param):
                path = path.replace(f"{{{path_param}}}", str(param_value))
                del arguments[path_param]

        response = request_method(url=f"{BASE_URL}{path}", params=arguments)
        response.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(response.json(), ensure_ascii=False, indent=2))]
    except Exception as e:
        logger.exception(f"Error calling tool `{name}`:")
        return [types.TextContent(type="text", text=f"Error calling tool `{name}`:\n{e}")]


async def run_server():
    logger.info("Running server...")
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="mcp-camara",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


def main():
    import asyncio

    asyncio.run(run_server())


if __name__ == "__main__":
    main()
