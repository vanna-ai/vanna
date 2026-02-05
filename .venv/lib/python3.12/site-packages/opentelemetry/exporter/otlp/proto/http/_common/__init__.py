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

from os import environ
from typing import Literal, Optional

import requests

from opentelemetry.sdk.environment_variables import (
    _OTEL_PYTHON_EXPORTER_OTLP_HTTP_CREDENTIAL_PROVIDER,
    _OTEL_PYTHON_EXPORTER_OTLP_HTTP_LOGS_CREDENTIAL_PROVIDER,
    _OTEL_PYTHON_EXPORTER_OTLP_HTTP_METRICS_CREDENTIAL_PROVIDER,
    _OTEL_PYTHON_EXPORTER_OTLP_HTTP_TRACES_CREDENTIAL_PROVIDER,
)
from opentelemetry.util._importlib_metadata import entry_points


def _is_retryable(resp: requests.Response) -> bool:
    if resp.status_code == 408:
        return True
    if resp.status_code >= 500 and resp.status_code <= 599:
        return True
    return False


def _load_session_from_envvar(
    cred_envvar: Literal[
        _OTEL_PYTHON_EXPORTER_OTLP_HTTP_LOGS_CREDENTIAL_PROVIDER,
        _OTEL_PYTHON_EXPORTER_OTLP_HTTP_TRACES_CREDENTIAL_PROVIDER,
        _OTEL_PYTHON_EXPORTER_OTLP_HTTP_METRICS_CREDENTIAL_PROVIDER,
    ],
) -> Optional[requests.Session]:
    _credential_env = environ.get(
        _OTEL_PYTHON_EXPORTER_OTLP_HTTP_CREDENTIAL_PROVIDER
    ) or environ.get(cred_envvar)
    if _credential_env:
        try:
            maybe_session = next(
                iter(
                    entry_points(
                        group="opentelemetry_otlp_credential_provider",
                        name=_credential_env,
                    )
                )
            ).load()()
        except StopIteration:
            raise RuntimeError(
                f"Requested component '{_credential_env}' not found in "
                f"entry point 'opentelemetry_otlp_credential_provider'"
            )
        if isinstance(maybe_session, requests.Session):
            return maybe_session
        else:
            raise RuntimeError(
                f"Requested component '{_credential_env}' is of type {type(maybe_session)}"
                f" must be of type `requests.Session`."
            )
    return None
