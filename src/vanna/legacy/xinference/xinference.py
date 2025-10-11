from xinference_client.client.restful.restful_client import (
  Client,
  RESTfulChatModelHandle,
)

from ..base import VannaBase


class Xinference(VannaBase):
    def __init__(self, config=None):
        VannaBase.__init__(self, config=config)

        if not config or "base_url" not in config:
            raise ValueError("config must contain at least Xinference base_url")

        base_url = config["base_url"]
        api_key = config.get("api_key", "not empty")
        self.xinference_client = Client(base_url=base_url, api_key=api_key)

    def system_message(self, message: str) -> any:
        return {"role": "system", "content": message}

    def user_message(self, message: str) -> any:
        return {"role": "user", "content": message}

    def assistant_message(self, message: str) -> any:
        return {"role": "assistant", "content": message}

    def submit_prompt(self, prompt, **kwargs) -> str:
        if prompt is None:
            raise Exception("Prompt is None")

        if len(prompt) == 0:
            raise Exception("Prompt is empty")

        num_tokens = 0
        for message in prompt:
            num_tokens += len(message["content"]) / 4

        model_uid = kwargs.get("model_uid") or self.config.get("model_uid", None)
        if model_uid is None:
            raise ValueError("model_uid is required")

        xinference_model = self.xinference_client.get_model(model_uid)
        if isinstance(xinference_model, RESTfulChatModelHandle):
            print(
                f"Using model_uid {model_uid} for {num_tokens} tokens (approx)"
            )

            response = xinference_model.chat(prompt)
            return response["choices"][0]["message"]["content"]
        else:
            raise NotImplementedError(f"Xinference model handle type {type(xinference_model)} is not supported, required RESTfulChatModelHandle")
