from __future__ import annotations
from typing import List
from dataclasses import dataclass

@dataclass
class Status:
    success: bool
    message: str

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

@dataclass
class Organization:
    name: str
    user: str | None
    connection: Connection | None

@dataclass
class QuestionId:
    id: str

@dataclass
class Question:
    question: str

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