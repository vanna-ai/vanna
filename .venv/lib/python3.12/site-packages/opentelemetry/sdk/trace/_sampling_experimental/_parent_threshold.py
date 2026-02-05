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
from opentelemetry.trace import Link, SpanKind, TraceState, get_current_span
from opentelemetry.util.types import Attributes

from ._composable import ComposableSampler, SamplingIntent
from ._trace_state import OtelTraceState
from ._util import (
    INVALID_THRESHOLD,
    MIN_THRESHOLD,
    is_valid_threshold,
)


class _ComposableParentThreshold(ComposableSampler):
    def __init__(self, root_sampler: ComposableSampler):
        self._root_sampler = root_sampler
        self._description = f"ComposableParentThreshold{{root={root_sampler.get_description()}}}"

    def sampling_intent(
        self,
        parent_ctx: Context | None,
        name: str,
        span_kind: SpanKind | None,
        attributes: Attributes,
        links: Sequence[Link] | None,
        trace_state: TraceState | None = None,
    ) -> SamplingIntent:
        parent_span = get_current_span(parent_ctx)
        parent_span_ctx = parent_span.get_span_context()
        is_root = not parent_span_ctx.is_valid
        if is_root:
            return self._root_sampler.sampling_intent(
                parent_ctx, name, span_kind, attributes, links, trace_state
            )

        ot_trace_state = OtelTraceState.parse(trace_state)

        if is_valid_threshold(ot_trace_state.threshold):
            return SamplingIntent(
                threshold=ot_trace_state.threshold,
                threshold_reliable=True,
            )

        threshold = (
            MIN_THRESHOLD
            if parent_span_ctx.trace_flags.sampled
            else INVALID_THRESHOLD
        )
        return SamplingIntent(threshold=threshold, threshold_reliable=False)

    def get_description(self) -> str:
        return self._description


def composable_parent_threshold(
    root_sampler: ComposableSampler,
) -> ComposableSampler:
    """Returns a consistent sampler that respects the sampling decision of
    the parent span or falls-back to the given sampler if it is a root span.

    - For spans without a parent context, delegate to the root sampler
    - For spans with a parent context, returns a SamplingIntent that propagates the parent's sampling decision
    - Returns the parent's threshold if available; otherwise, if the parent's sampled flag is set,
    returns threshold=0; otherwise, if the parent's sampled flag is not set, no threshold is returned.
    - Sets threshold_reliable to match the parent’s reliability, which is true if the parent had a threshold.
    - Does not add any attributes

    Args:
        root_sampler: The root sampler to use for spans without a parent context.
    """
    return _ComposableParentThreshold(root_sampler)
