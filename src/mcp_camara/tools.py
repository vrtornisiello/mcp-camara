from loguru import logger
from mcp import types

from mcp_camara.models import Endpoint
from mcp_camara.utils import singularize


def get_prefix(endpoint: Endpoint) -> str:
    method = endpoint.method

    if method == "GET":
        if endpoint.path.endswith("}"):
            return "get"
        return "list"
    elif method == "POST":
        return "create"
    elif method in {"PUT", "PATCH"}:
        return "update"
    elif method == "DELETE":
        return "delete"

    return ""


def get_tool_name(endpoint: Endpoint) -> str:
    prefix = get_prefix(endpoint)

    path_parts = [part for part in endpoint.path.split("/") if part]

    if path_parts[-1].endswith("}"):
        param = path_parts[-1][1:-1]
        resource = singularize(path_parts[-2])
        return f"{prefix}_{resource}_by_{param}"

    for i, part in enumerate(path_parts):
        if part.endswith("}"):
            resource = path_parts[i+1]
            parent_resource = singularize(path_parts[i-1])
            return f"{prefix}_{resource}_by_{parent_resource}"

    return f"{prefix}_" + "_".join(path_parts)


def create_tools(endpoints: list[Endpoint]) -> list[types.Tool]:
    logger.info("Creating tools...")
    tools = []

    for endpoint in endpoints:
        name = get_tool_name(endpoint)

        properties = {}
        required = []

        for parameter in endpoint.parameters:
            props = {
                "type": parameter.schema.type,
                "description": parameter.description,
            }

            if parameter.schema.format:
                props["format"] = parameter.schema.format

            properties[parameter.name] = props

            if parameter.required:
                required.append(parameter.name)

        tool = types.Tool(
            name=name,
            description=endpoint.description,
            inputSchema={
                "type": "object",
                "properties": properties,
                "required": required,
            },
            _meta={
                "path": endpoint.path,
                "method": endpoint.method
            }
        )

        tools.append(tool)
    logger.success("Tools created successfully.")
    return tools
