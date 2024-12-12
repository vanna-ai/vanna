import os

from ..base import VannaBase


class GoogleGeminiChat(VannaBase):
    def __init__(self, config=None):
        VannaBase.__init__(self, config=config)

        # default temperature - can be overrided using config
        self.temperature = 0.7

        if "temperature" in config:
            self.temperature = config["temperature"]

        if "model_name" in config:
            model_name = config["model_name"]
        else:
            model_name = "gemini-1.5-pro"

        self.google_api_key = None

        if "api_key" in config or os.getenv("GOOGLE_API_KEY"):
            """
            If Google api_key is provided through config
            or set as an environment variable, assign it.
            """
            import google.generativeai as genai

            genai.configure(api_key=config["api_key"])
            self.chat_model = genai.GenerativeModel(model_name)
        else:
            # Authenticate using VertexAI
            import google.auth
            import vertexai
            from vertexai.generative_models import GenerativeModel

            json_file_path = config.get("google_credentials")  # Assuming the JSON file path is provided in the config

            if not json_file_path or not os.path.exists(json_file_path):
                raise FileNotFoundError(f"JSON credentials file not found at: {json_file_path}")

            try:
                # Validate and set the JSON file path for GOOGLE_APPLICATION_CREDENTIALS
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = json_file_path

                # Initialize VertexAI with the credentials
                credentials, _ = google.auth.default()
                vertexai.init(credentials=credentials)
                self.chat_model = GenerativeModel(model_name)
            except google.auth.exceptions.DefaultCredentialsError as e:
                raise RuntimeError(f"Default credentials error: {e}")
            except google.auth.exceptions.TransportError as e:
                raise RuntimeError(f"Transport error during authentication: {e}")
            except Exception as e:
                raise RuntimeError(f"Failed to authenticate using JSON file: {e}")

    def system_message(self, message: str) -> any:
        return message

    def user_message(self, message: str) -> any:
        return message

    def assistant_message(self, message: str) -> any:
        return message

    def submit_prompt(self, prompt, **kwargs) -> str:
        response = self.chat_model.generate_content(
            prompt,
            generation_config={
                "temperature": self.temperature,
            },
        )
        return response.text
