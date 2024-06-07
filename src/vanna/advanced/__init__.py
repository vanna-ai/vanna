from abc import ABC, abstractmethod


class VannaAdvanced(ABC):
    def __init__(self, config=None):
        self.config = config

    @abstractmethod
    def get_function(self, question: str, additional_data: dict = {}) -> dict:
        pass

    @abstractmethod
    def create_function(self, question: str, sql: str, plotly_code: str, **kwargs) -> dict:
        pass

    @abstractmethod
    def update_function(self, old_function_name: str, updated_function: dict) -> bool:
        pass

    @abstractmethod
    def delete_function(self, function_name: str) -> bool:
        pass

    @abstractmethod
    def get_all_functions(self) -> list:
        pass
