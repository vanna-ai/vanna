"""Plotly-based chart generator with automatic chart type selection."""
from typing import Dict, Any, List
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio


class PlotlyChartGenerator:
    """Generate Plotly charts using heuristics based on DataFrame characteristics."""

    # Vanna brand colors from landing page
    THEME_COLORS = {
        'navy': '#023d60',
        'cream': '#e7e1cf',
        'teal': '#15a8a8',
        'orange': '#fe5d26',
        'magenta': '#bf1363'
    }

    # Color palette for charts (excluding cream as it's too light for data)
    COLOR_PALETTE = ['#15a8a8', '#fe5d26', '#bf1363', '#023d60']

    def generate_chart(self, df: pd.DataFrame, title: str = "Chart") -> Dict[str, Any]:
        """Generate a Plotly chart based on DataFrame shape and types.

        Heuristics:
        - 4+ columns: table
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

        # Heuristic: If 4 or more columns, render as a table
        if len(df.columns) >= 4:
            fig = self._create_table(df, title)
            result: Dict[str, Any] = json.loads(pio.to_json(fig))
            return result

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
        """Apply consistent Vanna brand styling to all charts.

        Uses Vanna brand colors from the landing page for a cohesive look.

        Args:
            fig: Plotly figure to update

        Returns:
            Updated figure with Vanna brand styling
        """
        fig.update_layout(
            # paper_bgcolor='white',
            # plot_bgcolor='white',
            font={'color': self.THEME_COLORS['navy']},  # Navy for text
            autosize=True,  # Allow chart to resize responsively
            colorway=self.COLOR_PALETTE,  # Use Vanna brand colors for data
            # Don't set width/height - let frontend handle sizing
        )
        return fig

    def _create_histogram(self, df: pd.DataFrame, column: str, title: str) -> go.Figure:
        """Create a histogram for a single numeric column."""
        fig = px.histogram(df, x=column, title=title, color_discrete_sequence=[self.THEME_COLORS['teal']])
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
        fig = px.bar(agg_df, x=x_col, y=y_col, title=title, color_discrete_sequence=[self.THEME_COLORS['orange']])
        fig.update_layout(
            xaxis_title=x_col,
            yaxis_title=y_col
        )
        self._apply_standard_layout(fig)
        return fig

    def _create_scatter_plot(self, df: pd.DataFrame, x_col: str, y_col: str, title: str) -> go.Figure:
        """Create a scatter plot for two numeric columns."""
        fig = px.scatter(df, x=x_col, y=y_col, title=title, color_discrete_sequence=[self.THEME_COLORS['magenta']])
        fig.update_layout(
            xaxis_title=x_col,
            yaxis_title=y_col
        )
        self._apply_standard_layout(fig)
        return fig

    def _create_correlation_heatmap(self, df: pd.DataFrame, columns: List[str], title: str) -> go.Figure:
        """Create a correlation heatmap for multiple numeric columns."""
        corr_matrix = df[columns].corr()
        # Custom Vanna color scale: navy (negative) -> cream (neutral) -> teal (positive)
        vanna_colorscale = [
            [0.0, self.THEME_COLORS['navy']],
            [0.5, self.THEME_COLORS['cream']],
            [1.0, self.THEME_COLORS['teal']]
        ]
        fig = px.imshow(
            corr_matrix,
            title=title,
            labels=dict(color="Correlation"),
            x=columns,
            y=columns,
            color_continuous_scale=vanna_colorscale,
            zmin=-1,
            zmax=1
        )
        self._apply_standard_layout(fig)
        return fig

    def _create_time_series_chart(self, df: pd.DataFrame, time_col: str, value_cols: List[str], title: str) -> go.Figure:
        """Create a time series line chart."""
        fig = go.Figure()

        for i, col in enumerate(value_cols[:5]):  # Limit to 5 lines for readability
            color = self.COLOR_PALETTE[i % len(self.COLOR_PALETTE)]
            fig.add_trace(go.Scatter(
                x=df[time_col],
                y=df[col],
                mode='lines',
                name=col,
                line=dict(color=color)
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
                barmode='group',
                color_discrete_sequence=self.COLOR_PALETTE
            )
            self._apply_standard_layout(fig)
            return fig
        else:
            # Single categorical: value counts
            counts = df[categorical_cols[0]].value_counts().reset_index()
            counts.columns = [categorical_cols[0], 'count']
            fig = px.bar(counts, x=categorical_cols[0], y='count', title=title, color_discrete_sequence=[self.THEME_COLORS['teal']])
            self._apply_standard_layout(fig)
            return fig

    def _create_generic_chart(self, df: pd.DataFrame, col1: str, col2: str, title: str) -> go.Figure:
        """Create a generic chart for any two columns."""
        # Try to determine the best representation
        if pd.api.types.is_numeric_dtype(df[col1]) and pd.api.types.is_numeric_dtype(df[col2]):
            return self._create_scatter_plot(df, col1, col2, title)
        else:
            # Treat first as categorical, second as value
            fig = px.bar(df, x=col1, y=col2, title=title, color_discrete_sequence=[self.THEME_COLORS['orange']])
            self._apply_standard_layout(fig)
            return fig

    def _create_table(self, df: pd.DataFrame, title: str) -> go.Figure:
        """Create a Plotly table for DataFrames with 4 or more columns."""
        # Prepare header
        header_values = list(df.columns)

        # Prepare cell values (transpose to get columns)
        cell_values = [df[col].tolist() for col in df.columns]

        # Create the table
        fig = go.Figure(data=[go.Table(
            header=dict(
                values=header_values,
                fill_color=self.THEME_COLORS['navy'],
                font=dict(color='white', size=12),
                align='left'
            ),
            cells=dict(
                values=cell_values,
                fill_color=[[self.THEME_COLORS['cream'] if i % 2 == 0 else 'white' for i in range(len(df))]],
                font=dict(color=self.THEME_COLORS['navy'], size=11),
                align='left'
            )
        )])

        fig.update_layout(
            title=title,
            font={'color': self.THEME_COLORS['navy']}
        )

        return fig
