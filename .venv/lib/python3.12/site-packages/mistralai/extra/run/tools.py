import inspect
import itertools
import json
import logging
from dataclasses import dataclass
from typing import Any, Callable, ForwardRef, Sequence, cast, get_type_hints

import opentelemetry.semconv._incubating.attributes.gen_ai_attributes as gen_ai_attributes
from griffe import (
    Docstring,
    DocstringSectionKind,
    DocstringSectionText,
    DocstringParameter,
    DocstringSection,
)
from opentelemetry import trace
from pydantic import Field, create_model
from pydantic.fields import FieldInfo

from mistralai.extra.exceptions import RunException
from mistralai.extra.mcp.base import MCPClientProtocol
from mistralai.extra.observability.otel import GenAISpanEnum, MistralAIAttributes, set_available_attributes
from mistralai.extra.run.result import RunOutputEntries
from mistralai.models import (
    FunctionResultEntry,
    FunctionTool,
    Function,
    FunctionCallEntry,
)


logger = logging.getLogger(__name__)


@dataclass
class RunFunction:
    name: str
    callable: Callable
    tool: FunctionTool


@dataclass
class RunCoroutine:
    name: str
    awaitable: Callable
    tool: FunctionTool


@dataclass
class RunMCPTool:
    name: str
    tool: FunctionTool
    mcp_client: MCPClientProtocol


RunTool = RunFunction | RunCoroutine | RunMCPTool


def _get_function_description(docstring_sections: list[DocstringSection]) -> str:
    """Given a list of docstring sections create a description for the function."""
    text_sections: list[DocstringSectionText] = []
    for section in docstring_sections:
        if section.kind == DocstringSectionKind.text:
            text_sections.append(cast(DocstringSectionText, section))
    return "\n".join(text.value for text in text_sections)


def _get_function_parameters(
    docstring_sections: list[DocstringSection],
    params_from_sig: list[inspect.Parameter],
    type_hints: dict[str, Any],
):
    """Given a list of docstring sections and type annotations create the most accurate tool parameters"""
    params_from_docstrings: list[DocstringParameter] = list(
        itertools.chain.from_iterable(
            section.value
            for section in docstring_sections
            if section.kind
            in (DocstringSectionKind.parameters, DocstringSectionKind.other_parameters)
        )
    )

    # Extract all description and annotation
    param_descriptions = {}
    param_annotations = {}

    for param_doc in params_from_docstrings:
        param_descriptions[param_doc.name] = param_doc.description

    for param in params_from_sig:
        if param.name not in param_descriptions:
            param_descriptions[param.name] = ""
        param_annotations[param.name] = type_hints.get(param.name)

    # resolve all params into Field and create the parameters schema
    fields: dict[str, tuple[type, FieldInfo]] = {}
    for p in params_from_sig:
        default = p.default if p.default is not inspect.Parameter.empty else ...
        annotation = (
            p.annotation if p.annotation is not inspect.Parameter.empty else Any
        )
        # handle forward ref with the help of get_type_hints
        if isinstance(annotation, str):
            annotation = type_hints[p.name]

        if isinstance(default, FieldInfo):
            field_info = default
        else:
            # If the annotation is Annotated[..., Field(...)] extract the Field and annotation
            # Otherwise, just use the annotation as-is
            field_info = None
            # If it's Annotated[..., SomeFieldMarker(...)], find it
            if hasattr(annotation, "__metadata__") and hasattr(annotation, "__args__"):
                # It's Annotated
                # e.g. Annotated[str, Field(...)]
                # Extract the first Field(...) or None if not found
                for meta in annotation.__metadata__:  # type: ignore
                    if isinstance(meta, FieldInfo):
                        field_info = meta
                        break
                # The actual annotation is the first part of Annotated
                annotation = annotation.__args__[0]  # type: ignore

                # handle forward ref with the help of get_type_hints
                if isinstance(annotation, ForwardRef):
                    annotation = param_annotations[p.name]

        # no Field
        if field_info is None:
            if default is ...:
                field_info = Field()
            else:
                field_info = Field(default=default)

        field_info.description = param_descriptions[p.name]
        fields[p.name] = (cast(type, annotation), field_info)

    schema = create_model("_", **fields).model_json_schema()  # type: ignore[call-overload]
    schema.pop("title", None)
    for prop in schema.get("properties", {}).values():
        prop.pop("title", None)
    return schema


def create_tool_call(func: Callable) -> FunctionTool:
    """Parse a function docstring / type annotations to create a FunctionTool."""
    name = func.__name__

    # Inspect and parse the docstring of the function
    doc = inspect.getdoc(func)
    docstring_sections: list[DocstringSection]
    if not doc:
        logger.warning(
            f"Function '{name}' without a docstring is being parsed, add docstring for more accurate result."
        )
        docstring_sections = []
    else:
        docstring = Docstring(doc, parser="google")
        docstring_sections = docstring.parse(warnings=False)
        if len(docstring_sections) == 0:
            logger.warning(
                f"Function '{name}' has no relevant docstring sections, add docstring for more accurate result."
            )

    # Extract the function's signature and type hints
    sig = inspect.signature(func)
    params_from_sig = list(sig.parameters.values())
    type_hints = get_type_hints(func, include_extras=True, localns=None, globalns=None)

    return FunctionTool(
        type="function",
        function=Function(
            name=name,
            description=_get_function_description(docstring_sections),
            parameters=_get_function_parameters(
                docstring_sections=docstring_sections,
                params_from_sig=params_from_sig,
                type_hints=type_hints,
            ),
            strict=True,
        ),
    )


async def create_function_result(
    function_call: FunctionCallEntry,
    run_tool: RunTool,
    continue_on_fn_error: bool = False,
) -> FunctionResultEntry:
    """Run the function with arguments of a FunctionCallEntry."""
    arguments = (
        json.loads(function_call.arguments)
        if isinstance(function_call.arguments, str)
        else function_call.arguments
    )
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span(GenAISpanEnum.function_call(function_call.name)) as span:
        try:
            if isinstance(run_tool, RunFunction):
                res = run_tool.callable(**arguments)
            elif isinstance(run_tool, RunCoroutine):
                res = await run_tool.awaitable(**arguments)
            elif isinstance(run_tool, RunMCPTool):
                res = await run_tool.mcp_client.execute_tool(function_call.name, arguments)
            function_call_attributes = {
                    gen_ai_attributes.GEN_AI_OPERATION_NAME: gen_ai_attributes.GenAiOperationNameValues.EXECUTE_TOOL.value,
                    gen_ai_attributes.GEN_AI_TOOL_CALL_ID: function_call.id,
                    MistralAIAttributes.MISTRAL_AI_TOOL_CALL_ARGUMENTS: str(function_call.arguments),
                    gen_ai_attributes.GEN_AI_TOOL_NAME: function_call.name
                }
            set_available_attributes(span, function_call_attributes)
        except Exception as e:
            if continue_on_fn_error is True:
                return FunctionResultEntry(
                    tool_call_id=function_call.tool_call_id,
                    result=f"Error while executing {function_call.name}: {str(e)}",
                )
            raise RunException(
                f"Failed to execute tool {function_call.name} with arguments '{function_call.arguments}'"
            ) from e

    return FunctionResultEntry(
        tool_call_id=function_call.tool_call_id,
        result=res if isinstance(res, str) else json.dumps(res),
    )


def get_function_calls(
    output_entries: Sequence[RunOutputEntries],
) -> list[FunctionCallEntry]:
    """Extract all FunctionCallEntry from a conversation response"""
    function_calls = []
    for entry in output_entries:
        if isinstance(entry, FunctionCallEntry):
            function_calls.append(entry)
    return function_calls
