from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Union


@dataclass
class Status:
    success: bool
    message: str


@dataclass
class StatusWithId:
    success: bool
    message: str
    id: str


@dataclass
class QuestionList:
    questions: List[FullQuestionDocument]


@dataclass
class FullQuestionDocument:
    id: QuestionId
    question: Question
    answer: SQLAnswer | None
    data: DataResult | None
    plotly: PlotlyResult | None


@dataclass
class QuestionSQLPair:
    question: str
    sql: str
    tag: Union[str, None]


@dataclass
class Organization:
    name: str
    user: str | None
    connection: Connection | None


@dataclass
class OrganizationList:
    organizations: List[str]


@dataclass
class QuestionStringList:
    questions: List[str]


@dataclass
class Visibility:
    visibility: bool


@dataclass
class UserEmail:
    email: str


@dataclass
class NewOrganization:
    org_name: str
    db_type: str


@dataclass
class NewOrganizationMember:
    org_name: str
    email: str
    is_admin: bool


@dataclass
class UserOTP:
    email: str
    otp: str


@dataclass
class ApiKey:
    key: str


@dataclass
class QuestionId:
    id: str


@dataclass
class Question:
    question: str


@dataclass
class QuestionCategory:
    question: str
    category: str

    NO_SQL_GENERATED = "No SQL Generated"
    SQL_UNABLE_TO_RUN = "SQL Unable to Run"
    BOOTSTRAP_TRAINING_QUERY = "Bootstrap Training Query"
    SQL_RAN = "SQL Ran Successfully"
    FLAGGED_FOR_REVIEW = "Flagged for Review"
    REVIEWED_AND_APPROVED = "Reviewed and Approved"
    REVIEWED_AND_REJECTED = "Reviewed and Rejected"
    REVIEWED_AND_UPDATED = "Reviewed and Updated"


@dataclass
class AccuracyStats:
    num_questions: int
    data: Dict[str, int]


@dataclass
class Followup:
    followup: str


@dataclass
class QuestionEmbedding:
    question: Question
    embedding: List[float]


@dataclass
class Connection:
    # TODO: implement
    pass


@dataclass
class SQLAnswer:
    raw_answer: str
    prefix: str
    postfix: str
    sql: str


@dataclass
class Explanation:
    explanation: str


@dataclass
class DataResult:
    question: str | None
    sql: str | None
    table_markdown: str
    error: str | None
    correction_attempts: int


@dataclass
class PlotlyResult:
    plotly_code: str


@dataclass
class WarehouseDefinition:
    name: str
    tables: List[TableDefinition]


@dataclass
class TableDefinition:
    schema_name: str
    table_name: str
    ddl: str | None
    columns: List[ColumnDefinition]


@dataclass
class ColumnDefinition:
    name: str
    type: str
    is_primary_key: bool
    is_foreign_key: bool
    foreign_key_table: str
    foreign_key_column: str


@dataclass
class Diagram:
    raw: str
    mermaid_code: str


@dataclass
class StringData:
    data: str


@dataclass
class DataFrameJSON:
    data: str


@dataclass
class TrainingData:
    questions: List[dict]
    ddl: List[str]
    documentation: List[str]


@dataclass
class TrainingPlanItem:
    item_type: str
    item_group: str
    item_name: str
    item_value: str

    def __str__(self):
        if self.item_type == self.ITEM_TYPE_SQL:
            return f"Train on SQL: {self.item_group} {self.item_name}"
        elif self.item_type == self.ITEM_TYPE_DDL:
            return f"Train on DDL: {self.item_group} {self.item_name}"
        elif self.item_type == self.ITEM_TYPE_IS:
            return f"Train on Information Schema: {self.item_group} {self.item_name}"

    ITEM_TYPE_SQL = "sql"
    ITEM_TYPE_DDL = "ddl"
    ITEM_TYPE_IS = "is"


class TrainingPlan:
    """
    A class representing a training plan. You can see what's in it, and remove items from it that you don't want trained.

    **Example:**
    ```python
    plan = vn.get_training_plan()

    plan.get_summary()
    ```

    """

    _plan: List[TrainingPlanItem]

    def __init__(self, plan: List[TrainingPlanItem]):
        self._plan = plan

    def __str__(self):
        return "\n".join(self.get_summary())

    def __repr__(self):
        return self.__str__()

    def get_summary(self) -> List[str]:
        """
        **Example:**
        ```python
        plan = vn.get_training_plan()

        plan.get_summary()
        ```

        Get a summary of the training plan.

        Returns:
            List[str]: A list of strings describing the training plan.
        """

        return [f"{item}" for item in self._plan]

    def remove_item(self, item: str):
        """
        **Example:**
        ```python
        plan = vn.get_training_plan()

        plan.remove_item("Train on SQL: What is the average salary of employees?")
        ```

        Remove an item from the training plan.

        Args:
            item (str): The item to remove.
        """
        for plan_item in self._plan:
            if str(plan_item) == item:
                self._plan.remove(plan_item)
                break
