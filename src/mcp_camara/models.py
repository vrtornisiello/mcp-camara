from typing import Any, Optional

from pydantic import BaseModel, Field


class ParameterSchema(BaseModel):
    """Defines the schema of a single API parameter."""

    type: str = Field(description="The data type of the parameter.")
    format: Optional[str] = Field(default=None, description="An optional format specifier for the data type.")
    default: Optional[Any] = Field(default=None, description="The default value for the parameter if none is provided.")


class Parameter(BaseModel):
    """Represents a single parameter for an endpoint."""

    name: str = Field(description="The name of the parameter.")
    description: Optional[str] = Field(default=None, description="The human-readable description of the parameter's purpose.")
    required: bool = Field(description="A boolean indicating whether the parameter is required for the endpoint call.")
    schema: ParameterSchema = Field(description="The schema defining the type, format, and default value of the parameter.")


class EndpointSummary(BaseModel):
    """A summary of an API endpoint, containing basic identifying information."""

    path: str = Field(description="The URL path of the endpoint, which may include path parameters.")
    method: str = Field(description="The HTTP method for the endpoint.")
    description: Optional[str] = Field(default=None, description="The human-readable description of what the endpoint does.")


class Endpoint(EndpointSummary):
    """Represents a full API endpoint, including its summary and all of its parameters."""

    parameters: list[Parameter] = Field(description="A list of parameters that the endpoint accepts.")
