"""DataFrame component for displaying tabular data."""

from typing import Any, Dict, List, Optional
from pydantic import Field
from ....core.rich_component import RichComponent, ComponentType


class DataFrameComponent(RichComponent):
    """DataFrame component specifically for displaying tabular data from SQL queries and similar sources."""

    type: ComponentType = ComponentType.DATAFRAME
    rows: List[Dict[str, Any]] = Field(default_factory=list)  # List of row dictionaries
    columns: List[str] = Field(default_factory=list)  # Column names in display order
    title: Optional[str] = None
    description: Optional[str] = None
    row_count: int = 0
    column_count: int = 0

    # Display options
    max_rows_displayed: int = 100  # Limit rows shown in UI
    searchable: bool = True
    sortable: bool = True
    filterable: bool = True
    exportable: bool = True  # Allow export to CSV/Excel

    # Styling options
    striped: bool = True
    bordered: bool = True
    compact: bool = False

    # Pagination
    paginated: bool = True
    page_size: int = 25

    # Data types for better formatting (optional)
    column_types: Dict[str, str] = Field(default_factory=dict)  # column_name -> "string"|"number"|"date"|"boolean"

    def __init__(self, **kwargs: Any) -> None:
        # Set defaults before calling super().__init__
        if 'rows' not in kwargs:
            kwargs['rows'] = []
        if 'columns' not in kwargs:
            kwargs['columns'] = []
        if 'column_types' not in kwargs:
            kwargs['column_types'] = {}

        super().__init__(**kwargs)

        # Auto-calculate counts if not provided
        if self.rows and len(self.rows) > 0:
            if 'row_count' not in kwargs:
                self.row_count = len(self.rows)
            if not self.columns and self.rows:
                self.columns = list(self.rows[0].keys())
            if 'column_count' not in kwargs:
                self.column_count = len(self.columns)
        else:
            if 'row_count' not in kwargs:
                self.row_count = 0
            if 'column_count' not in kwargs:
                self.column_count = len(self.columns) if self.columns else 0

    @classmethod
    def from_records(
        cls,
        records: List[Dict[str, Any]],
        title: Optional[str] = None,
        description: Optional[str] = None,
        **kwargs: Any
    ) -> "DataFrameComponent":
        """Create a DataFrame component from a list of record dictionaries."""
        columns = list(records[0].keys()) if records else []

        # Ensure we pass the required arguments correctly
        component_data = {
            'rows': records,
            'columns': columns,
            'row_count': len(records),
            'column_count': len(columns),
            'column_types': {},  # Initialize empty dict
        }

        if title is not None:
            component_data['title'] = title
        if description is not None:
            component_data['description'] = description

        # Merge with any additional kwargs
        component_data.update(kwargs)

        return cls(**component_data)
