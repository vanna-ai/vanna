from typing import Any, TypeVar

from pydantic import BaseModel
from ...models import JSONSchema, ResponseFormat
from ._pydantic_helper import rec_strict_json_schema

CustomPydanticModel = TypeVar("CustomPydanticModel", bound=BaseModel)


def response_format_from_pydantic_model(
    model: type[CustomPydanticModel],
) -> ResponseFormat:
    """Generate a strict JSON schema from a pydantic model."""
    model_schema = rec_strict_json_schema(model.model_json_schema())
    json_schema = JSONSchema.model_validate(
        {"name": model.__name__, "schema": model_schema, "strict": True}
    )
    return ResponseFormat(type="json_schema", json_schema=json_schema)


def pydantic_model_from_json(
    json_data: dict[str, Any],
    pydantic_model: type[CustomPydanticModel],
) -> CustomPydanticModel:
    """Parse a JSON schema into a pydantic model."""
    return pydantic_model.model_validate(json_data)
