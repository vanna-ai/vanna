# THIS FILE IS THE EXACT COPY OF THE ORIGINAL FILE FROM src/mistralai/_hooks/custom_user_agent.py
from typing import Union

import httpx

from .types import BeforeRequestContext, BeforeRequestHook

PREFIX = "mistral-client-python/"

class CustomUserAgentHook(BeforeRequestHook):
    def before_request(
        self, hook_ctx: BeforeRequestContext, request: httpx.Request
    ) -> Union[httpx.Request, Exception]:
        current = request.headers["user-agent"]
        if current.startswith(PREFIX):
            return request
        
        request.headers["user-agent"] = (
            PREFIX + current.split(" ")[1]
        )

        return request
