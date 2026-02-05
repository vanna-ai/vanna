from typing import Optional

MIGRATION_MESSAGE = "This client is deprecated. To migrate to the new client, please refer to this guide: https://github.com/mistralai/client-python/blob/main/MIGRATION.md. If you need to use this client anyway, pin your version to 0.4.2."


class MistralClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: str = "",
        max_retries: int = 5,
        timeout: int = 120,
    ):
        raise NotImplementedError(MIGRATION_MESSAGE)
