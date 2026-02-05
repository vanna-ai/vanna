from typing import Any


def rec_strict_json_schema(schema_node: Any) -> Any:
    """
    Recursively set the additionalProperties property to False for all objects in the JSON Schema.
    This makes the JSON Schema strict (i.e. no additional properties are allowed).
    """
    if isinstance(schema_node, (str, bool)) or schema_node is None:
        return schema_node
    if isinstance(schema_node, dict):
        if "type" in schema_node and schema_node["type"] == "object":
            schema_node["additionalProperties"] = False
        for key, value in schema_node.items():
            schema_node[key] = rec_strict_json_schema(value)
    elif isinstance(schema_node, list):
        for i, value in enumerate(schema_node):
            schema_node[i] = rec_strict_json_schema(value)
    else:
        raise ValueError(f"Unexpected type: {schema_node}")
    return schema_node
