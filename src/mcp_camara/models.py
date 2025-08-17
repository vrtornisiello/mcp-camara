from typing import Any, Optional

from pydantic import BaseModel


class ParameterSchema(BaseModel):
    type: str
    format: Optional[str] = None
    default: Optional[Any] = None

class Parameter(BaseModel):
    name: str
    description: Optional[str] = None
    required: bool
    schema: ParameterSchema

class Endpoint(BaseModel):
    path: str
    method: str
    description: Optional[str] = None
    parameters: list[Parameter]
