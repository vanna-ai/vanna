"""Plotly-based chart generator with automatic chart type selection."""
from typing import Dict, Any, List
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio


class PlotlyChartGenerator:
    """Generate Plotly charts using heuristics based on DataFrame characteristics."""

    def generate_chart(self, df: pd.DataFrame, title: str = "Chart") -> Dict[str, Any]:
        """Generate a Plotly chart based on DataFrame shape and types.

        Heuristics:
        - 1 numeric column: histogram
        - 2 columns (1 categorical, 1 numeric): bar chart
        - 2 numeric columns: scatter plot
        - 3+ numeric columns: correlation heatmap or multi-line chart
        - Time series data: line chart
        - Multiple categorical: grouped bar chart

        Args:
            df: DataFrame to visualize
            title: Title for the chart

        Returns:
            Plotly figure as dictionary

        Raises:
            ValueError: If DataFrame is empty or cannot be visualized
        """
        if df.empty:
            raise ValueError("Cannot visualize empty DataFrame")

        # Identify column types
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()

        # Check for time series
        is_timeseries = len(datetime_cols) > 0

        # Apply heuristics
        if is_timeseries and len(numeric_cols) > 0:
            # Time series line chart
            fig = self._create_time_series_chart(df, datetime_cols[0], numeric_cols, title)
        elif len(numeric_cols) == 1 and len(categorical_cols) == 0:
            # Single numeric column: histogram
            fig = self._create_histogram(df, numeric_cols[0], title)
        elif len(numeric_cols) == 1 and len(categorical_cols) == 1:
            # One categorical, one numeric: bar chart
            fig = self._create_bar_chart(df, categorical_cols[0], numeric_cols[0], title)
        elif len(numeric_cols) == 2:
            # Two numeric columns: scatter plot
            fig = self._create_scatter_plot(df, numeric_cols[0], numeric_cols[1], title)
        elif len(numeric_cols) >= 3:
            # Multiple numeric columns: correlation heatmap
            fig = self._create_correlation_heatmap(df, numeric_cols, title)
        elif len(categorical_cols) >= 2:
            # Multiple categorical: grouped bar chart
            fig = self._create_grouped_bar_chart(df, categorical_cols, title)
        else:
            # Fallback: show first two columns as scatter/bar
            if len(df.columns) >= 2:
                fig = self._create_generic_chart(df, df.columns[0], df.columns[1], title)
            else:
                raise ValueError("Cannot determine appropriate visualization for this DataFrame")

        # Convert to JSON-serializable dict using plotly's JSON encoder
        result: Dict[str, Any] = json.loads(pio.to_json(fig))
        return result

    def _apply_standard_layout(self, fig: go.Figure) -> go.Figure:
        """Apply consistent white background and dark text to all charts.

        This ensures charts look good in any theme context without needing
        to detect or adapt to the frontend theme.

        Args:
            fig: Plotly figure to update

        Returns:
            Updated figure with standard layout
        """
        fig.update_layout(
            paper_bgcolor='white',
            plot_bgcolor='white',
            font={'color': '#1f2937'},  # Dark gray for readability
            autosize=True,  # Allow chart to resize responsively
            # Don't set width/height - let frontend handle sizing
        )
        return fig

    def _create_histogram(self, df: pd.DataFrame, column: str, title: str) -> go.Figure:
        """Create a histogram for a single numeric column."""
        fig = px.histogram(df, x=column, title=title)
        fig.update_layout(
            xaxis_title=column,
            yaxis_title="Count",
            showlegend=False
        )
        self._apply_standard_layout(fig)
        return fig

    def _create_bar_chart(self, df: pd.DataFrame, x_col: str, y_col: str, title: str) -> go.Figure:
        """Create a bar chart for categorical vs numeric data."""
        # Aggregate if needed
        agg_df = df.groupby(x_col)[y_col].sum().reset_index()
        fig = px.bar(agg_df, x=x_col, y=y_col, title=title)
        fig.update_layout(
            xaxis_title=x_col,
            yaxis_title=y_col
        )
        self._apply_standard_layout(fig)
        return fig

    def _create_scatter_plot(self, df: pd.DataFrame, x_col: str, y_col: str, title: str) -> go.Figure:
        """Create a scatter plot for two numeric columns."""
        fig = px.scatter(df, x=x_col, y=y_col, title=title)
        fig.update_layout(
            xaxis_title=x_col,
            yaxis_title=y_col
        )
        self._apply_standard_layout(fig)
        return fig

    def _create_correlation_heatmap(self, df: pd.DataFrame, columns: List[str], title: str) -> go.Figure:
        """Create a correlation heatmap for multiple numeric columns."""
        corr_matrix = df[columns].corr()
        fig = px.imshow(
            corr_matrix,
            title=title,
            labels=dict(color="Correlation"),
            x=columns,
            y=columns,
            color_continuous_scale='RdBu_r',
            zmin=-1,
            zmax=1
        )
        self._apply_standard_layout(fig)
        return fig

    def _create_time_series_chart(self, df: pd.DataFrame, time_col: str, value_cols: List[str], title: str) -> go.Figure:
        """Create a time series line chart."""
        fig = go.Figure()

        for col in value_cols[:5]:  # Limit to 5 lines for readability
            fig.add_trace(go.Scatter(
                x=df[time_col],
                y=df[col],
                mode='lines',
                name=col
            ))

        fig.update_layout(
            title=title,
            xaxis_title=time_col,
            yaxis_title="Value",
            hovermode='x unified'
        )
        self._apply_standard_layout(fig)
        return fig

    def _create_grouped_bar_chart(self, df: pd.DataFrame, categorical_cols: List[str], title: str) -> go.Figure:
        """Create a grouped bar chart for multiple categorical columns."""
        # Use first two categorical columns
        if len(categorical_cols) >= 2:
            # Count occurrences
            grouped = df.groupby(categorical_cols[:2]).size().reset_index(name='count')
            fig = px.bar(
                grouped,
                x=categorical_cols[0],
                y='count',
                color=categorical_cols[1],
                title=title,
                barmode='group'
            )
            self._apply_standard_layout(fig)
            return fig
        else:
            # Single categorical: value counts
            counts = df[categorical_cols[0]].value_counts().reset_index()
            counts.columns = [categorical_cols[0], 'count']
            fig = px.bar(counts, x=categorical_cols[0], y='count', title=title)
            self._apply_standard_layout(fig)
            return fig

    def _create_generic_chart(self, df: pd.DataFrame, col1: str, col2: str, title: str) -> go.Figure:
        """Create a generic chart for any two columns."""
        # Try to determine the best representation
        if pd.api.types.is_numeric_dtype(df[col1]) and pd.api.types.is_numeric_dtype(df[col2]):
            return self._create_scatter_plot(df, col1, col2, title)
        else:
            # Treat first as categorical, second as value
            fig = px.bar(df, x=col1, y=col2, title=title)
            self._apply_standard_layout(fig)
            return fig
