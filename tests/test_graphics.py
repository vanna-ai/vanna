import pandas as pd

from vanna.base.base import VannaBase


class DummyVanna(VannaBase):
    # Minimal concrete implementation to allow instantiation
    def generate_embedding(self, data: str, **kwargs):
        return []

    def get_similar_question_sql(self, question: str, **kwargs):
        return []

    def get_related_ddl(self, question: str, **kwargs):
        return []

    def get_related_documentation(self, question: str, **kwargs):
        return []

    def add_question_sql(self, question: str, sql: str, **kwargs):
        return ""

    def add_ddl(self, ddl: str, **kwargs):
        return ""

    def add_documentation(self, documentation: str, **kwargs):
        return ""

    def get_training_data(self, **kwargs):
        return pd.DataFrame()

    def remove_training_data(self, id: str, **kwargs):
        return True

    def system_message(self, message: str):
        return message

    def user_message(self, message: str):
        return message

    def assistant_message(self, message: str):
        return message

    def submit_prompt(self, prompt, **kwargs):
        # Not used in this test
        return ""


def test_categorical_only_uses_counts_in_chart():
    vn = DummyVanna()
    df = pd.DataFrame({"animal": ["cat", "dog", "cat", "bird", "dog", "dog"]})
    # Intentionally pass bad code to trigger fallback
    fig = vn.get_plotly_figure(plotly_code="raise Exception('force fallback')", df=df, dark_mode=False)
    # The fallback should aggregate counts for categorical-only data
    assert fig is not None
    # Extract values from the first trace
    trace = fig.data[0]
    # Plotly pie or bar will store counts in 'values' (pie) or 'y' (bar)
    values = getattr(trace, "values", None)
    if values is None:
        values = getattr(trace, "y", None)
    # The counts should be [3, 2, 1] for dog, cat, bird in some order
    vals_sorted = sorted(list(values))
    assert vals_sorted == [1, 2, 3]