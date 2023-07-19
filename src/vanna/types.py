from __future__ import annotations
from typing import List, Dict, Union
from dataclasses import dataclass

@dataclass
class Status:
    success: bool
    message: str

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
    #TODO: implement
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