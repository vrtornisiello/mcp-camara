import re
from datetime import date
from typing import Any

import httpx
from loguru import logger
from mcp.server.fastmcp import FastMCP

from mcp_camara.models import APIResponse, EndpointSummary
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
async def list_endpoints() -> APIResponse:
    """Lists available endpoints for the Brazilian Chamber of Deputies API.

    This is the primary discovery tool to understand the API's capabilities.
    It returns a list of all available operations, including the `path`, `method`,
    and `description` for each.

    Use the `path` and `method` from an endpoint in this list to either fetch
    its detailed parameter schema with the `get_endpoint_schema` tool or to
    execute it with the `call_endpoint` tool.

    Returns:
        APIResponse: An APIResponse object containing a list of `EndpointSummary` objects.
    """
    return APIResponse(status="success", results=endpoints_summary)


@mcp.tool()
async def get_endpoint_schema(path: str, method: str) -> APIResponse:
    """Retrieves the detailed schema for a single API endpoint.

    Use this tool to understand exactly how to call a specific endpoint,
    including its required and optional parameters.

    The `path` and `method` must be a valid combination obtained from the
    `list_api_endpoints` tool.

    Args:
        path (str): The endpoint path (e.g., '/deputados/{id}').
        method (str): The endpoint method (e.g., 'GET').

    Returns:
        APIResponse: An APIResponse object containing the Endpoint schema on success, or an error message.
    """
    key = f"{method.upper()}:{path}"

    endpoint = endpoints_mapping.get(key)

    if endpoint is None:
        return APIResponse(
            status="error",
            error_details={
                "message": (
                    f"Endpoint '{method} {path}' not found. "
                    "Please use the `list_endpoints` tool to find a valid path and method combination."
                )
            }
        )

    return APIResponse(status="success", results=endpoint)


@mcp.tool()
async def call_endpoint(path: str, method: str, params: dict[str, Any]) -> APIResponse:
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
        APIResponse: An APIResponse object containing the requested data on success, or an error message.
    """
    method_upper = method.upper()

    if method_upper != "GET":
        return APIResponse(
            status="error",
            error_details={
                "message": (
                    f"Invalid method: `{method}`. Only 'GET' is supported."
                    "Please use the `list_endpoints` tool to find a valid path and method combination."
                )
            }
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

        return APIResponse(status="success", results=response.json())
    except httpx.HTTPStatusError as e:
        logger.exception("Error calling tool `call_endpoint`:")
        if e.response.status_code == httpx.codes.BAD_REQUEST:
            return APIResponse(
                status="error",
                error_details={
                    "status_code": "400 Bad Request",
                    "message": (
                        f"Client error '400 Bad Request' for url {e.request.url}. "
                        "Check the endpoint schema using the `get_endpoint_schema` tool."
                    )
                }
            )
        else:
            return APIResponse(status="error", error_details={"message": str(e)})
    except Exception as e:
        logger.exception("Error calling tool `call_endpoint`:")
        return APIResponse(status="error", error_details={"message": str(e)})


@mcp.tool()
async def get_deputy_by_name(name: str) -> APIResponse:
    """Retrieves a list of deputies by name.

    This is a helper tool that abstracts the process of querying for a deputy by name.

    Args:
        name (str): The name of the deputy to search for.

    Returns:
        APIResponse: An APIResponse object containing a list of deputies on success, or an error message.
    """
    return await call_endpoint(
        path="/deputados",
        method="GET",
        params={"nome": name},
    )


@mcp.tool()
async def get_deputy_expenses(
    name: str | None = None,
    id: int | None = None,
    year: int | None = None,
    month: int | None = None
) -> APIResponse:
    """Gets the expenses for a single deputy, specified by name or ID.

    This tool finds a deputy by their name or ID.
    You must provide either `name` or `id`. If `name` is used and multiple
    deputies are found, it will return an error asking for a more specific name or an ID.
    Optional `year` and `month` parameters can be used to filter expenses.

    Args:
        name (str | None): The full or partial name of the deputy.
        id (int | None): The unique ID of the deputy.
        year (int | None): The year to filter expenses by.
        month (int | None): The month to filter expenses by.

    Returns:
        APIResponse: An APIResponse object containing the deputy's expense data on success, or an error message.
    """
    deputy_id = id

    if deputy_id is None:
        if not name:
            return APIResponse(
                status="error",
                error_details={
                    "message": "You must provide either a `name` or an `id`."
                }
            )

        deputies_response = await get_deputy_by_name(name)

        if deputies_response.status == "error":
            return deputies_response

        deputies = deputies_response.results.get("dados", [])

        if not deputies:
            return APIResponse(
                status="error",
                error_details={
                    "message": f"No deputy found with name containing '{name}'."
                }
            )

        if len(deputies) > 1:
            suggestions = [f"'{d['nome']}' (ID: {d['id']})" for d in deputies]
            return APIResponse(
                status="error",
                error_details={
                    "message": (
                        f"Multiple deputies found for '{name}'. "
                        f"Please be more specific or use an ID. Suggestions: {', '.join(suggestions)}."
                    )
                }
            )

        deputy_id = deputies[0]["id"]

    params = {}

    if year:
        params["ano"] = year
    if month:
        params["mes"] = month

    return await call_endpoint(
        path=f"/deputados/{deputy_id}/despesas",
        method="GET",
        params=params,
    )


@mcp.tool()
async def get_bills_by_deputy(deputy_id: int, years: list[str] | None = None) -> APIResponse:
    """Retrieves a list of bills (proposições) by a specific author.

    This is a helper tool that abstracts the process of querying bills for a deputy.

    Args:
        deputy_id (int): The ID of the deputy authoring the bill.
        years (list[str] | None): One or more years for when bills were presented.
            If set to None, the current year is used. Defaults to None.

    Returns:
        APIResponse: An APIResponse object containing a list of bills on success, or an error message.
    """
    params = {}

    if deputy_id:
        params["idDeputadoAutor"] = deputy_id
    else:
        return APIResponse(
            status="error",
            error_details={"message": "You must provide `deputy_id`."}
        )

    if years:
        params["ano"] = ",".join(years)
    else:
        current_year = date.today().year
        params["ano"] = current_year

    return await call_endpoint(
        path="/proposicoes",
        method="GET",
        params=params,
    )


def main():
    logger.info("Running server...")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
