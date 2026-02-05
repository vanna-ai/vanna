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

from functools import cache

# FIXME: Use importlib.metadata (not importlib_metadata)
# when support for 3.11 is dropped if the rest of
# the supported versions at that time have the same API.
from importlib_metadata import (  # type: ignore
    Distribution,
    EntryPoint,
    EntryPoints,
    PackageNotFoundError,
    distributions,
    requires,
    version,
)
from importlib_metadata import (
    entry_points as original_entry_points,
)


@cache
def _original_entry_points_cached():
    return original_entry_points()


def entry_points(**params):
    """Replacement for importlib_metadata.entry_points that caches getting all the entry points.

    That part can be very slow, and OTel uses this function many times."""
    return _original_entry_points_cached().select(**params)


__all__ = [
    "entry_points",
    "version",
    "EntryPoint",
    "EntryPoints",
    "requires",
    "Distribution",
    "distributions",
    "PackageNotFoundError",
]
