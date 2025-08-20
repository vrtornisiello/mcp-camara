import json
import re
from typing import Any

import httpx
from loguru import logger
from mcp.server.fastmcp import FastMCP

from mcp_camara.models import Endpoint, EndpointSummary
from mcp_camara.parser import get_endpoints, load_openapi_spec

BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"
SPEC_URL = f"{BASE_URL}/api-docs"

spec = load_openapi_spec(SPEC_URL)

endpoints = get_endpoints(spec)

endpoints_summary = [
    EndpointSummary(
        path=endpoint.path,
        method=endpoint.method,
        description=endpoint.description
    ) for endpoint in endpoints
]

endpoints_mapping = {
    f"{endpoint.method}:{endpoint.path}": endpoint
    for endpoint in endpoints
}

mcp = FastMCP(name="mcp-camara")


@mcp.tool()
async def list_endpoints() -> list[EndpointSummary]:
    """Lists available endpoints for the Brazilian Chamber of Deputies API.

    This is the primary discovery tool to understand the API's capabilities.
    It returns a list of all available operations, including the `path`, `method`,
    and `description` for each.

    Use the `path` and `method` from an endpoint in this list to either fetch
    its detailed parameter schema with the `get_endpoint_schema` tool or to
    execute it with the `call_endpoint` tool.

    Returns:
        list[EndpointSummary]: A list of `EndpointSummary` objects, each containing
            an endpoint `path`, `method` and `description`.
    """
    return endpoints_summary


@mcp.tool()
async def get_endpoint_schema(path: str, method: str) -> Endpoint | str:
    """Retrieves the detailed schema for a single API endpoint.

    Use this tool to understand exactly how to call a specific endpoint,
    including its required and optional parameters.

    The `path` and `method` must be a valid combination obtained from the
    `list_api_endpoints` tool.

    The returned `Endpoint` object contains the parameter definitions needed
    to build the `params` argument for the `call_endpoint` tool.

    Args:
        path (str): The endpoint path (e.g., '/deputados/{id}').
        method (str): The endpoint method (e.g., 'GET').

    Returns:
        Endpoint: An `Endpoint` object, containing detailed information
            about the endpoint parameters.
    """
    key = f"{method.upper()}:{path}"

    endpoint = endpoints_mapping.get(key)

    if endpoint is None:
        return (
            f"Endpoint '{method} {path}' not found. "
            "Please use the `list_endpoints` tool to find a valid path and method combination."
        )

    return endpoint


@mcp.tool()
async def call_endpoint(path: str, method: str, params: dict[str, Any]) -> str:
    """Calls a specific endpoint of the Brazilian Chamber of Deputies API.

    This is the final tool in the workflow, used to retrieve the actual data.
    The `path` and `method` must be a valid combination obtained
    from the `list_api_endpoints` tool.

    The `params` dictionary must contain all required parameters for the chosen endpoint,
    as defined by the `get_endpoint_schema` tool. Both path parameters and query parameters
    are passed together in this single dictionary.

    Args:
        path (str): The endpoint path (e.g., '/deputados/{id}').
        method (str): The HTTP method (e.g., 'GET').
        params (dict[str, Any]): A dictionary of parameters for the endpoint.

    Returns:
        str: A JSON string containing the API response.
    """
    method_upper = method.upper()

    if method_upper != "GET":
        return (
            f"Invalid method: `{method}`. Only 'GET' is supported."
            "Please use the `list_endpoints` tool to find a valid path and method combination."
        )

    for path_param in re.findall(r"\{([^{}]+)\}", path):
        if param_value := params.get(path_param):
            path = path.replace(f"{{{path_param}}}", str(param_value))
            del params[path_param]

    try:
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method_upper,
                url=f"{BASE_URL}{path}",
                params=params
            )
            response.raise_for_status()
        return json.dumps(response.json(), ensure_ascii=False, indent=2)
    except Exception as e:
        logger.exception("Error calling tool `call_endpoint`:")
        return f"Error calling tool `call_endpoint`:\n {e}"


def main():
    logger.info("Running server...")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
