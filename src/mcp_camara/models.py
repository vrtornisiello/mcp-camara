from typing import Any, Literal, Optional, Self

from pydantic import BaseModel, Field, model_validator


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


class APIResponse(BaseModel):
    """A standardized response object for all tool outputs.

    This model provides a consistent structure for returning data from tools,
    clearly separating successful results from error information.
    """
    status: Literal["success", "error"] = Field(description="Indicates whether the tool call was successful.")
    results: Optional[Any] = Field(default=None, description="The successful result of the tool call. Only present if status is 'success'.")
    error_details: Optional[dict[str, Any]] = Field(default=None, description="A dictionary containing error details. Only present if status is 'error'.")

    @model_validator(mode="after")
    def check_passwords_match(self) -> Self:
        if (self.results is None) ^ (self.error_details is None):
            return self
        raise ValueError("Only one of 'results' or 'error_details' should be set")
