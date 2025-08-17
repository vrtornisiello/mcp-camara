from typing import Any

import httpx
from loguru import logger

from mcp_camara.models import Endpoint, Parameter

type APIPaths = dict[str, dict[str, dict]]


def load_openapi_spec(url: str) -> dict[str, Any]:
    logger.info(f"Loading spec from {url}")
    try:
        response = httpx.get(url)
        response.raise_for_status()
        logger.success(f"Spec load successfully.")
        return response.json()
    except Exception:
        logger.exception("Error loading spec:")


def get_endpoints(openapi_spec: dict[str, Any]) -> list[Endpoint]:
    logger.info("Parsing endpoints...")

    paths: APIPaths = openapi_spec.get("paths", {})
    endpoints = []

    for path, path_methods in paths.items():
        for method, method_details in path_methods.items():

            parameters: list[dict] = []
            for param in method_details.get("parameters", []):
                if param.get("in") in {"query", "path"}:
                    parameters.append(Parameter(**param))

            endpoint = Endpoint(
                path=path,
                method=method.upper(),
                description=method_details.get("description"),
                parameters=parameters
            )

            endpoints.append(endpoint)

    logger.success("Endpoints parsed successfully.")
    return endpoints
