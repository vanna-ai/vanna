from typing import Optional

from .client import MIGRATION_MESSAGE


class MistralAsyncClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: str = "",
        max_retries: int = 5,
        timeout: int = 120,
        max_concurrent_requests: int = 64,
    ):
        raise NotImplementedError(MIGRATION_MESSAGE)
