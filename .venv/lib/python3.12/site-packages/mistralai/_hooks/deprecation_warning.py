import logging
from typing import Union

import httpx

from .types import AfterSuccessContext, AfterSuccessHook

logger = logging.getLogger(__name__)

HEADER_MODEL_DEPRECATION_TIMESTAMP = "x-model-deprecation-timestamp"


class DeprecationWarningHook(AfterSuccessHook):

    def after_success(
        self, hook_ctx: AfterSuccessContext, response: httpx.Response
    ) -> Union[httpx.Response, Exception]:
        if HEADER_MODEL_DEPRECATION_TIMESTAMP in response.headers:
            model = response.json()["model"]
            # pylint: disable=logging-fstring-interpolation
            logger.warning(
                "WARNING: The model %s is deprecated and will be removed on %s. Please refer to https://docs.mistral.ai/getting-started/models/#api-versioning for more information.",
                model,
                response.headers[HEADER_MODEL_DEPRECATION_TIMESTAMP],
            )
        return response
