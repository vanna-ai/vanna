import copy
import json
import logging
import os
import traceback
from datetime import datetime, timezone
from enum import Enum

import httpx
import opentelemetry.semconv._incubating.attributes.gen_ai_attributes as gen_ai_attributes
import opentelemetry.semconv._incubating.attributes.http_attributes as http_attributes
import opentelemetry.semconv.attributes.server_attributes as server_attributes
from opentelemetry import propagate, trace
from opentelemetry.sdk.trace import SpanProcessor
from opentelemetry.trace import Span, Status, StatusCode, Tracer, set_span_in_context

logger = logging.getLogger(__name__)


OTEL_SERVICE_NAME: str = "mistralai_sdk"
MISTRAL_SDK_OTEL_TRACER_NAME: str = OTEL_SERVICE_NAME + "_tracer"

MISTRAL_SDK_DEBUG_TRACING: bool = os.getenv("MISTRAL_SDK_DEBUG_TRACING", "false").lower() == "true"
DEBUG_HINT: str = "To see detailed tracing logs, set MISTRAL_SDK_DEBUG_TRACING=true."


class MistralAIAttributes:
    MISTRAL_AI_TOTAL_TOKENS = "mistral_ai.request.total_tokens"
    MISTRAL_AI_TOOL_CALL_ARGUMENTS = "mistral_ai.tool.call.arguments"
    MISTRAL_AI_MESSAGE_ID = "mistral_ai.message.id"
    MISTRAL_AI_OPERATION_NAME= "mistral_ai.operation.name"
    MISTRAL_AI_OCR_USAGE_PAGES_PROCESSED = "mistral_ai.ocr.usage.pages_processed"
    MISTRAL_AI_OCR_USAGE_DOC_SIZE_BYTES = "mistral_ai.ocr.usage.doc_size_bytes"
    MISTRAL_AI_OPERATION_ID = "mistral_ai.operation.id"
    MISTRAL_AI_ERROR_TYPE = "mistral_ai.error.type"
    MISTRAL_AI_ERROR_MESSAGE = "mistral_ai.error.message"
    MISTRAL_AI_ERROR_CODE = "mistral_ai.error.code"
    MISTRAL_AI_FUNCTION_CALL_ARGUMENTS = "mistral_ai.function.call.arguments"

class MistralAINameValues(Enum):
    OCR = "ocr"

class TracingErrors(Exception, Enum):
    FAILED_TO_CREATE_SPAN_FOR_REQUEST = "Failed to create span for request."
    FAILED_TO_ENRICH_SPAN_WITH_RESPONSE = "Failed to enrich span with response."
    FAILED_TO_HANDLE_ERROR_IN_SPAN = "Failed to handle error in span."
    FAILED_TO_END_SPAN = "Failed to end span."

    def __str__(self):
        return str(self.value)

class GenAISpanEnum(str, Enum):
    CONVERSATION = "conversation"
    CONV_REQUEST = "POST /v1/conversations"
    EXECUTE_TOOL = "execute_tool"
    VALIDATE_RUN = "validate_run"

    @staticmethod
    def function_call(func_name: str):
        return f"function_call[{func_name}]"


def parse_time_to_nanos(ts: str) -> int:
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc)
    return int(dt.timestamp() * 1e9)

def set_available_attributes(span: Span, attributes: dict) -> None:
    for attribute, value in attributes.items():
        if value:
            span.set_attribute(attribute, value)


def enrich_span_from_request(span: Span, request: httpx.Request) -> Span:
    if not request.url.port:
        # From httpx doc:
        # Note that the URL class performs port normalization as per the WHATWG spec.
        # Default ports for "http", "https", "ws", "wss", and "ftp" schemes are always treated as None.
        # Handling default ports since most of the time we are using https
        if request.url.scheme == "https":
            port = 443
        elif request.url.scheme == "http":
            port = 80
        else:
            port = -1
    else:
        port = request.url.port

    span.set_attributes({
        http_attributes.HTTP_REQUEST_METHOD: request.method,
        http_attributes.HTTP_URL: str(request.url),
        server_attributes.SERVER_ADDRESS: request.headers.get("host", ""),
        server_attributes.SERVER_PORT: port
    })
    if request._content:
        request_body = json.loads(request._content)

        attributes = {
            gen_ai_attributes.GEN_AI_REQUEST_CHOICE_COUNT: request_body.get("n", None),
            gen_ai_attributes.GEN_AI_REQUEST_ENCODING_FORMATS: request_body.get("encoding_formats", None),
            gen_ai_attributes.GEN_AI_REQUEST_FREQUENCY_PENALTY: request_body.get("frequency_penalty", None),
            gen_ai_attributes.GEN_AI_REQUEST_MAX_TOKENS: request_body.get("max_tokens", None),
            gen_ai_attributes.GEN_AI_REQUEST_MODEL: request_body.get("model", None),
            gen_ai_attributes.GEN_AI_REQUEST_PRESENCE_PENALTY: request_body.get("presence_penalty", None),
            gen_ai_attributes.GEN_AI_REQUEST_SEED: request_body.get("random_seed", None),
            gen_ai_attributes.GEN_AI_REQUEST_STOP_SEQUENCES: request_body.get("stop", None),
            gen_ai_attributes.GEN_AI_REQUEST_TEMPERATURE: request_body.get("temperature", None),
            gen_ai_attributes.GEN_AI_REQUEST_TOP_P: request_body.get("top_p", None),
            gen_ai_attributes.GEN_AI_REQUEST_TOP_K: request_body.get("top_k", None),
            # Input messages are likely to be large, containing user/PII data and other sensitive information.
            # Also structured attributes are not yet supported on spans in Python.
            # For those reasons, we will not record the input messages for now.
            gen_ai_attributes.GEN_AI_INPUT_MESSAGES: None,
        }
        # Set attributes only if they are not None.
        # From OpenTelemetry documentation: None is not a valid attribute value per spec / is not a permitted value type for an attribute.
        set_available_attributes(span, attributes)
    return span


def enrich_span_from_response(tracer: trace.Tracer, span: Span, operation_id: str, response: httpx.Response) -> None:
    span.set_status(Status(StatusCode.OK))
    response_data = json.loads(response.content)

    # Base attributes
    attributes: dict[str, str | int] = {
        http_attributes.HTTP_RESPONSE_STATUS_CODE: response.status_code,
        MistralAIAttributes.MISTRAL_AI_OPERATION_ID: operation_id,
        gen_ai_attributes.GEN_AI_PROVIDER_NAME: gen_ai_attributes.GenAiProviderNameValues.MISTRAL_AI.value
    }

    # Add usage attributes if available
    usage = response_data.get("usage", {})
    if usage:
        attributes.update({
            gen_ai_attributes.GEN_AI_USAGE_PROMPT_TOKENS: usage.get("prompt_tokens", 0),
            gen_ai_attributes.GEN_AI_USAGE_OUTPUT_TOKENS: usage.get("completion_tokens", 0),
            MistralAIAttributes.MISTRAL_AI_TOTAL_TOKENS: usage.get("total_tokens", 0)
        })

    span.set_attributes(attributes)
    if operation_id == "agents_api_v1_agents_create":
        # Semantics from https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-agent-spans/#create-agent-span
        agent_attributes = {
            gen_ai_attributes.GEN_AI_OPERATION_NAME: gen_ai_attributes.GenAiOperationNameValues.CREATE_AGENT.value,
            gen_ai_attributes.GEN_AI_AGENT_DESCRIPTION: response_data.get("description", ""),
            gen_ai_attributes.GEN_AI_AGENT_ID: response_data.get("id", ""),
            gen_ai_attributes.GEN_AI_AGENT_NAME: response_data.get("name", ""),
            gen_ai_attributes.GEN_AI_REQUEST_MODEL: response_data.get("model", ""),
            gen_ai_attributes.GEN_AI_SYSTEM_INSTRUCTIONS: response_data.get("instructions", "")
        }
        span.set_attributes(agent_attributes)
    if operation_id in ["agents_api_v1_conversations_start", "agents_api_v1_conversations_append"]:
        outputs = response_data.get("outputs", [])
        conversation_attributes = {
            gen_ai_attributes.GEN_AI_OPERATION_NAME: gen_ai_attributes.GenAiOperationNameValues.INVOKE_AGENT.value,
            gen_ai_attributes.GEN_AI_CONVERSATION_ID: response_data.get("conversation_id", "")
        }
        span.set_attributes(conversation_attributes)
        parent_context = set_span_in_context(span)

        for output in outputs:
            # TODO: Only enrich the spans if it's a single turn conversation.
            # Multi turn conversations are handled in the extra.run.tools.create_function_result function
            if output["type"] == "function.call":
                pass
            if output["type"] == "tool.execution":
                start_ns = parse_time_to_nanos(output["created_at"])
                end_ns = parse_time_to_nanos(output["completed_at"])
                child_span = tracer.start_span("Tool Execution", start_time=start_ns, context=parent_context)
                child_span.set_attributes({"agent.trace.public": ""})
                tool_attributes = {
                    gen_ai_attributes.GEN_AI_OPERATION_NAME: gen_ai_attributes.GenAiOperationNameValues.EXECUTE_TOOL.value,
                    gen_ai_attributes.GEN_AI_TOOL_CALL_ID: output.get("id", ""),
                    MistralAIAttributes.MISTRAL_AI_TOOL_CALL_ARGUMENTS: output.get("arguments", ""),
                    gen_ai_attributes.GEN_AI_TOOL_NAME: output.get("name", "")
                }
                child_span.set_attributes(tool_attributes)
                child_span.end(end_time=end_ns)
            if output["type"] == "message.output":
                start_ns = parse_time_to_nanos(output["created_at"])
                end_ns = parse_time_to_nanos(output["completed_at"])
                child_span = tracer.start_span("Message Output", start_time=start_ns, context=parent_context)
                child_span.set_attributes({"agent.trace.public": ""})
                message_attributes = {
                    gen_ai_attributes.GEN_AI_OPERATION_NAME: gen_ai_attributes.GenAiOperationNameValues.CHAT.value,
                    gen_ai_attributes.GEN_AI_PROVIDER_NAME: gen_ai_attributes.GenAiProviderNameValues.MISTRAL_AI.value,
                    MistralAIAttributes.MISTRAL_AI_MESSAGE_ID: output.get("id", ""),
                    gen_ai_attributes.GEN_AI_AGENT_ID: output.get("agent_id", ""),
                    gen_ai_attributes.GEN_AI_REQUEST_MODEL: output.get("model", "")
                }
                child_span.set_attributes(message_attributes)
                child_span.end(end_time=end_ns)
    if operation_id == "ocr_v1_ocr_post":
        usage_info = response_data.get("usage_info", "")
        ocr_attributes = {
            MistralAIAttributes.MISTRAL_AI_OPERATION_NAME: MistralAINameValues.OCR.value,
            MistralAIAttributes.MISTRAL_AI_OCR_USAGE_PAGES_PROCESSED: usage_info.get("pages_processed", "") if usage_info else "",
            MistralAIAttributes.MISTRAL_AI_OCR_USAGE_DOC_SIZE_BYTES: usage_info.get("doc_size_bytes", "") if usage_info else "",
            gen_ai_attributes.GEN_AI_REQUEST_MODEL: response_data.get("model", "")
        }
        span.set_attributes(ocr_attributes)


class GenAISpanProcessor(SpanProcessor):
    def on_start(self, span, parent_context = None):
        span.set_attributes({"agent.trace.public": ""})


def get_or_create_otel_tracer() -> tuple[bool, Tracer]:
    """
    Get a tracer from the current TracerProvider.

    The SDK does not set up its own TracerProvider - it relies on the application
    to configure OpenTelemetry. This follows OTEL best practices where:
    - Libraries/SDKs get tracers from the global provider
    - Applications configure the TracerProvider

    If no TracerProvider is configured, the ProxyTracerProvider (default) will
    return a NoOp tracer, effectively disabling tracing. Once the application
    sets up a real TracerProvider, subsequent spans will be recorded.

    Returns:
        Tuple[bool, Tracer]: (tracing_enabled, tracer)
            - tracing_enabled is True if a real TracerProvider is configured
            - tracer is always valid (may be NoOp if no provider configured)
    """
    tracer_provider = trace.get_tracer_provider()
    tracer = tracer_provider.get_tracer(MISTRAL_SDK_OTEL_TRACER_NAME)

    # Tracing is considered enabled if we have a real TracerProvider (not the default proxy)
    tracing_enabled = not isinstance(tracer_provider, trace.ProxyTracerProvider)

    return tracing_enabled, tracer

def get_traced_request_and_span(
    tracing_enabled: bool,
    tracer: Tracer,
    span: Span | None,
    operation_id: str,
    request: httpx.Request,
) -> tuple[httpx.Request, Span | None]:
        if not tracing_enabled:
            return request, span

        try:
            span = tracer.start_span(name=operation_id)
            span.set_attributes({"agent.trace.public": ""})
            # Inject the span context into the request headers to be used by the backend service to continue the trace
            propagate.inject(request.headers, context=set_span_in_context(span))
            span = enrich_span_from_request(span, request)
        except Exception:
            logger.warning(
                "%s %s",
                TracingErrors.FAILED_TO_CREATE_SPAN_FOR_REQUEST,
                traceback.format_exc() if MISTRAL_SDK_DEBUG_TRACING else DEBUG_HINT,
            )
            if span:
                end_span(span=span)
            span = None

        return request, span


def get_traced_response(
    tracing_enabled: bool,
    tracer: Tracer,
    span: Span | None,
    operation_id: str,
    response: httpx.Response,
) -> httpx.Response:
    if not tracing_enabled or not span:
        return response
    try:
        is_stream_response = not response.is_closed and not response.is_stream_consumed
        if is_stream_response:
            return TracedResponse.from_response(resp=response, span=span)
        enrich_span_from_response(
            tracer, span, operation_id, response
        )
    except Exception:
        logger.warning(
            "%s %s",
            TracingErrors.FAILED_TO_ENRICH_SPAN_WITH_RESPONSE,
            traceback.format_exc() if MISTRAL_SDK_DEBUG_TRACING else DEBUG_HINT,
        )
    if span:
        end_span(span=span)
    return response

def get_response_and_error(
    tracing_enabled: bool,
    tracer: Tracer,
    span: Span | None,
    operation_id: str,
    response: httpx.Response,
    error: Exception | None,
) -> tuple[httpx.Response, Exception | None]:
        if not tracing_enabled or not span:
            return response, error
        try:
            if error:
                span.record_exception(error)
                span.set_status(Status(StatusCode.ERROR, str(error)))
            if hasattr(response, "_content") and response._content:
                response_body = json.loads(response._content)
                if response_body.get("object", "") == "error":
                    if error_msg := response_body.get("message", ""):
                        attributes = {
                            http_attributes.HTTP_RESPONSE_STATUS_CODE: response.status_code,
                            MistralAIAttributes.MISTRAL_AI_ERROR_TYPE: response_body.get("type", ""),
                            MistralAIAttributes.MISTRAL_AI_ERROR_MESSAGE: error_msg,
                            MistralAIAttributes.MISTRAL_AI_ERROR_CODE: response_body.get("code", ""),
                        }
                        for attribute, value in attributes.items():
                            if value:
                                span.set_attribute(attribute, value)
            span.end()
            span = None
        except Exception:
            logger.warning(
                "%s %s",
                TracingErrors.FAILED_TO_HANDLE_ERROR_IN_SPAN,
                traceback.format_exc() if MISTRAL_SDK_DEBUG_TRACING else DEBUG_HINT,
            )

            if span:
                span.end()
                span = None
        return response, error


def end_span(span: Span) -> None:
    try:
        span.end()
    except Exception:
        logger.warning(
            "%s %s",
            TracingErrors.FAILED_TO_END_SPAN,
            traceback.format_exc() if MISTRAL_SDK_DEBUG_TRACING else DEBUG_HINT,
        )

class TracedResponse(httpx.Response):
    """
    TracedResponse is a subclass of httpx.Response that ends the span when the response is closed.

    This hack allows ending the span only once the stream is fully consumed.
    """
    def __init__(self, *args, span: Span | None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.span = span

    def close(self) -> None:
        if self.span:
            end_span(span=self.span)
        super().close()

    async def aclose(self) -> None:
        if self.span:
            end_span(span=self.span)
        await super().aclose()

    @classmethod
    def from_response(cls, resp: httpx.Response, span: Span | None) -> "TracedResponse":
        traced_resp = cls.__new__(cls)
        traced_resp.__dict__ = copy.copy(resp.__dict__)
        traced_resp.span = span

        # Warning: this syntax bypasses the __init__ method.
        # If you add init logic in the TracedResponse.__init__ method, you will need to add the following line for it to execute:
        # traced_resp.__init__(your_arguments)

        return traced_resp
