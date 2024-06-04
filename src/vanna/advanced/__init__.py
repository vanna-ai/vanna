from abc import ABC, abstractmethod


class VannaAdvanced(ABC):
    def __init__(self, vanna_kb: str, vanna_api_key: str, config=None):
        self.vanna_kb = vanna_kb
        self.vanna_api_key = vanna_api_key
        self.config = config

    @abstractmethod
    def get_function(self, question: str, additional_data: dict = {}) -> dict:
        pass

    @abstractmethod
    def create_function(self, question: str, sql: str, plotly_code: str, **kwargs) -> dict:
        pass
