# Copyright The OpenTelemetry Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

from typing import Sequence

from opentelemetry.context import Context
from opentelemetry.sdk.trace.sampling import Decision, Sampler, SamplingResult
from opentelemetry.trace import Link, SpanKind, TraceState
from opentelemetry.util.types import Attributes

from ._composable import ComposableSampler, SamplingIntent
from ._trace_state import OTEL_TRACE_STATE_KEY, OtelTraceState
from ._util import INVALID_THRESHOLD, is_valid_random_value, is_valid_threshold


class _CompositeSampler(Sampler):
    def __init__(self, delegate: ComposableSampler):
        self._delegate = delegate

    def should_sample(
        self,
        parent_context: Context | None,
        trace_id: int,
        name: str,
        kind: SpanKind | None = None,
        attributes: Attributes | None = None,
        links: Sequence[Link] | None = None,
        trace_state: TraceState | None = None,
    ) -> SamplingResult:
        ot_trace_state = OtelTraceState.parse(trace_state)

        intent = self._delegate.sampling_intent(
            parent_context, name, kind, attributes, links, trace_state
        )
        threshold = intent.threshold

        if is_valid_threshold(threshold):
            adjusted_count_correct = intent.threshold_reliable
            if is_valid_random_value(ot_trace_state.random_value):
                randomness = ot_trace_state.random_value
            else:
                # Use last 56 bits of trace_id as randomness
                randomness = trace_id & 0x00FFFFFFFFFFFFFF
            sampled = threshold <= randomness
        else:
            sampled = False
            adjusted_count_correct = False

        decision = Decision.RECORD_AND_SAMPLE if sampled else Decision.DROP
        if sampled and adjusted_count_correct:
            ot_trace_state.threshold = threshold
        else:
            ot_trace_state.threshold = INVALID_THRESHOLD

        return SamplingResult(
            decision,
            intent.attributes,
            _update_trace_state(trace_state, ot_trace_state, intent),
        )

    def get_description(self) -> str:
        return self._delegate.get_description()


def _update_trace_state(
    trace_state: TraceState | None,
    ot_trace_state: OtelTraceState,
    intent: SamplingIntent,
) -> TraceState | None:
    otts = ot_trace_state.serialize()
    if not trace_state:
        if otts:
            return TraceState(((OTEL_TRACE_STATE_KEY, otts),))
        return None
    new_trace_state = intent.update_trace_state(trace_state)
    if otts:
        return new_trace_state.update(OTEL_TRACE_STATE_KEY, otts)
    return new_trace_state


def composite_sampler(delegate: ComposableSampler) -> Sampler:
    """A sampler that uses a a composable sampler to make its decision while
    handling tracestate.

    Args:
        delegate: The composable sampler to use for making sampling decisions.
    """
    return _CompositeSampler(delegate)
