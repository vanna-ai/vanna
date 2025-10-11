"""Table component for displaying structured data."""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from ....core.rich_component import RichComponent, ComponentType


class TableColumn(BaseModel):
    """Column definition for table component."""

    key: str
    title: str
    width: Optional[Union[str, int]] = None
    align: str = "left"  # "left", "center", "right"
    sortable: bool = False
    filterable: bool = False


class TableComponent(RichComponent):
    """Table component for displaying structured data."""

    type: ComponentType = ComponentType.TABLE
    columns: List[TableColumn]
    rows: List[Dict[str, Any]] = Field(default_factory=list)
    title: Optional[str] = None
    searchable: bool = False
    sortable: bool = False
    paginated: bool = False
    page_size: int = 10
    striped: bool = True
    bordered: bool = True
