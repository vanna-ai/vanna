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

RANDOM_VALUE_BITS = 56
MAX_THRESHOLD = 1 << RANDOM_VALUE_BITS  # 0% sampling
MIN_THRESHOLD = 0  # 100% sampling
MAX_RANDOM_VALUE = MAX_THRESHOLD - 1
INVALID_THRESHOLD = -1
INVALID_RANDOM_VALUE = -1

_probability_threshold_scale = float.fromhex("0x1p56")


def calculate_threshold(sampling_probability: float) -> int:
    return MAX_THRESHOLD - round(
        sampling_probability * _probability_threshold_scale
    )


def is_valid_threshold(threshold: int) -> bool:
    return MIN_THRESHOLD <= threshold <= MAX_THRESHOLD


def is_valid_random_value(random_value: int) -> bool:
    return 0 <= random_value <= MAX_RANDOM_VALUE
