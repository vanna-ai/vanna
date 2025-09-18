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


def _extract_counts(fig):
    trace = fig.data[0]
    values = getattr(trace, "values", None)
    if values is None:
        values = getattr(trace, "y", None)
    return sorted(list(values))


def test_categorical_only_uses_counts_in_chart():
    vn = DummyVanna()
    df = pd.DataFrame({"animal": ["cat", "dog", "cat", "bird", "dog", "dog"]})
    # Intentionally pass bad code to trigger fallback
    fig = vn.get_plotly_figure(plotly_code="raise Exception('force fallback')", df=df, dark_mode=False)
    # The fallback should aggregate counts for categorical-only data
    assert fig is not None
    vals_sorted = _extract_counts(fig)
    # The counts should be [3, 2, 1] in some order
    assert vals_sorted == [1, 2, 3]


def test_categorical_only_overrides_llm_line_chart():
    vn = DummyVanna()
    df = pd.DataFrame({"animal": ["cat", "dog", "cat", "bird", "dog", "dog"]})
    # Provide a runnable line plot over the default index; our post-validation should override it
    fig = vn.get_plotly_figure(plotly_code="import plotly.express as px\nfig = px.line(df)", df=df, dark_mode=False)
    assert fig is not None
    vals_sorted = _extract_counts(fig)
    assert vals_sorted == [1, 2, 3]


def test_mixed_data_overrides_llm_line_chart_to_bar():
    vn = DummyVanna()
    df = pd.DataFrame({
        "category": ["A", "B", "C", "D"],
        "value": [10, 5, 3, 8]
    })
    # LLM returns a generic line over index; heuristic should switch to bar with x='category', y='value'
    fig = vn.get_plotly_figure(plotly_code="import plotly.express as px\nfig = px.line(df)", df=df, dark_mode=False)
    assert fig is not None
    # Validate the shape
    trace = fig.data[0]
    # Expect bar (has attribute 'type' == 'bar' or has 'y' equal to df['value'])
    y = getattr(trace, "y", None)
    assert y is not None
    assert list(y) == df["value"].tolist()