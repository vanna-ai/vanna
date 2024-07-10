from ..base import VannaBase

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    raise ImportError("Please install boto3 and botocore to use Amazon Bedrock models")

class Bedrock_Converse(VannaBase):
    def __init__(self, client=None, config=None):
        VannaBase.__init__(self, config=config)

        # default parameters
        self.temperature = 0.0
        self.max_tokens = 500
        
        if client is None:
            raise ValueError(
                "A valid Bedrock runtime client must be provided to invoke Bedrock models"
            )
        else:
            self.client = client
        
        if config is None:
            raise ValueError(
                "Config is required with model_id and inference parameters"
            )
        
        if "modelId" not in config:
            raise ValueError(
                "config must contain a modelId to invoke"
            )
        else:
            self.model = config["modelId"]
        
        if "temperature" in config:
            self.temperature = config["temperature"]
        
        if "max_tokens" in config:
            self.max_tokens = config["max_tokens"]

    def system_message(self, message: str) -> dict:
        return {"role": "system", "content": message}

    def user_message(self, message: str) -> dict:
        return {"role": "user", "content": message}

    def assistant_message(self, message: str) -> dict:
        return {"role": "assistant", "content": message}

    def submit_prompt(self, prompt, **kwargs) -> str:
        inference_config = {
            "temperature": self.temperature,
            "maxTokens": self.max_tokens
        }
        additional_model_fields = {
            "top_p": 1,  # setting top_p value for nucleus sampling
        }

        system_message = None
        no_system_prompt = []
        for prompt_message in prompt:
            role = prompt_message["role"]
            if role == "system":
                system_message = prompt_message["content"]
            else:
                no_system_prompt.append({"role": role, "content":[{"text": prompt_message["content"]}]})

        converse_api_params = {
            "modelId": self.model,
            "messages": no_system_prompt,
            "inferenceConfig": inference_config,
            "additionalModelRequestFields": additional_model_fields
        }

        if system_message:
            converse_api_params["system"] = [{"text": system_message}]

        try:
            response = self.client.converse(**converse_api_params)
            text_content = response["output"]["message"]["content"][0]["text"]
            return text_content
        except ClientError as err:
            message = err.response["Error"]["Message"]
            raise Exception(f"A Bedrock client error occurred: {message}")