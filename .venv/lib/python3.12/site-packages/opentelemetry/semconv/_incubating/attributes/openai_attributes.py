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

from enum import Enum
from typing import Final

OPENAI_REQUEST_SERVICE_TIER: Final = "openai.request.service_tier"
"""
The service tier requested. May be a specific tier, default, or auto.
"""

OPENAI_RESPONSE_SERVICE_TIER: Final = "openai.response.service_tier"
"""
The service tier used for the response.
"""

OPENAI_RESPONSE_SYSTEM_FINGERPRINT: Final = (
    "openai.response.system_fingerprint"
)
"""
A fingerprint to track any eventual change in the Generative AI environment.
"""


class OpenaiRequestServiceTierValues(Enum):
    AUTO = "auto"
    """The system will utilize scale tier credits until they are exhausted."""
    DEFAULT = "default"
    """The system will utilize the default scale tier."""
