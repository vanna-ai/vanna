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
from opentelemetry.trace import Link, SpanKind, TraceState
from opentelemetry.util.types import Attributes

from ._composable import ComposableSampler, SamplingIntent
from ._util import MIN_THRESHOLD

_intent = SamplingIntent(threshold=MIN_THRESHOLD)


class _ComposableAlwaysOnSampler(ComposableSampler):
    def sampling_intent(
        self,
        parent_ctx: Context | None,
        name: str,
        span_kind: SpanKind | None,
        attributes: Attributes,
        links: Sequence[Link] | None,
        trace_state: TraceState | None = None,
    ) -> SamplingIntent:
        return _intent

    def get_description(self) -> str:
        return "ComposableAlwaysOn"


_always_on = _ComposableAlwaysOnSampler()


def composable_always_on() -> ComposableSampler:
    """Returns a composable sampler that samples all spans.

    - Always returns a SamplingIntent with threshold set to sample all spans (threshold = 0)
    - Sets threshold_reliable to true
    - Does not add any attributes
    """
    return _always_on
