import json
from datetime import date
from typing import Callable, Dict, Iterable, List, Optional, Set

import numpy as np
import requests
import rich
import sqlparse
from pydantic import Field
from sklearn.metrics import hamming_loss, jaccard_score

# pip install "trulens-eval==0.19.2"
# pip install "litellm=1.21.7"
from trulens_eval import Feedback, LiteLLM, Select, Tru
from trulens_eval.feedback import Groundedness, GroundTruthAgreement, prompts
from trulens_eval.tru_custom_app import TruCustomApp, instrument
from trulens_eval.utils.generated import re_0_10_rating

# From Vanna commit: e995493bcd189f3052c99ea8295c789a6de1aeea
from vanna.chromadb.chromadb_vector import ChromaDB_VectorStore
from vanna.ollama import Ollama

# Initialise Tru (see more https://www.trulens.org/trulens_eval/install/)
tru = Tru()
tru.reset_database()
tru.run_dashboard()


class OllamaLocalDB(ChromaDB_VectorStore, Ollama):
    """Locally served LLM, and vector database"""

    def __init__(self, config: dict):
        Ollama.__init__(self, config=config)
        ChromaDB_VectorStore.__init__(self, config=config)
        self.config: dict
        self.call_log = []

    def submit_prompt(self, prompt, **kwargs) -> str:
        url = "http://localhost:11434/api/generate"

        payload = {
            "model": self.config["model"].split("/")[-1],  # or "llama2",
            "prompt": prompt[0]["content"] + prompt[1]["content"],
            "stream": False,
        }

        payload_json = json.dumps(payload)
        headers = {"Content-Type": "application/json"}

        response = requests.post(url, data=payload_json, headers=headers)
        json_response = response.json()
        self.call_log.append((payload_json, json_response))

        return json_response["response"]


# Make sure these methods are tracked in the dashboard, and can have metrics for their results
instrument.method(OllamaLocalDB, "get_related_documentation")
instrument.method(OllamaLocalDB, "get_similar_question_sql")
instrument.method(OllamaLocalDB, "get_related_ddl")
instrument.method(OllamaLocalDB, "generate_sql")


class StandAloneProvider(LiteLLM):
    """Inherits from LiteLLM to access the Ollama models.

    Adds functionality to evaluate Vanna-specific performance.
    """

    ground_truth_prompts: List[dict]
    possible_table_names: Optional[List[str]] = Field(default=None)
    table_name_indicies: Optional[Dict[str, int]] = Field(default=None)
    dbpath: str

    def __init__(self, *args, **kwargs):
        # TODO: why was self_kwargs required here independently of kwargs?
        self_kwargs = dict()
        self_kwargs.update(**kwargs)
        # All database table names that the app has access to.
        if self_kwargs["possible_table_names"] is not None:
            self_kwargs["table_name_indicies"] = {
                table_name: i
                for i, table_name in enumerate(self_kwargs["possible_table_names"])
            }

        super().__init__(**self_kwargs)  # need to include pydantic.BaseModel.__init__

    def jacard_matching_tables(self, user_query, retrieved_tables):
        """Measures the similarity between the predicted set of labels and the true set of labels.
        It is calculated as the size of the intersection divided by the size of the union of the two label sets.
        """
        return self.matching_tables(user_query, retrieved_tables, metric="jacard")

    def exact_match_matching_tables(self, user_query, retrieved_tables):
        """Instances where the predicted labels exactly match the true labels. This must be performed on a per-instance
        basis (with all predicted tables and all actual tables).

        Extracts the table names from the `NodeWithScore` objects.
        """
        tables = []
        for retrieval in retrieved_tables:
            tables.append(retrieval["node"]["metadata"]["name"])
        return self.matching_tables(
            user_query, retrieved_tables=tables, metric="exact_match"
        )

    def matching_tables(
        self, user_query: str, retrieved_tables: Iterable[str], metric="hamming_loss"
    ) -> float:
        """Multi label classification for a single instance. `metric`'s available: hamming_loss, jacard_similarity"""
        if self.table_name_indicies is None:
            raise ValueError("possible_table_names must be set")

        # get the first (and only) expected tables that matches the ground truth data
        actual_tables = [
            data["tables"]
            for data in self.ground_truth_prompts
            if data["query"] == user_query
        ][0]

        # Binary vectors to represent the tables
        # create a binary valued vector from the possible table names indicies
        y_pred = [int(t in retrieved_tables) for t in self.table_name_indicies]
        y_true = [int(t in actual_tables) for t in self.table_name_indicies]

        if metric == "hamming_loss":
            # Penalises equally false negatives (when a table didnt occur, but should have)
            # and positives (when a table occured, but shouldnt have)
            score = float(1 - hamming_loss(y_pred=y_pred, y_true=y_true))
            return score

        if metric == "jacard_similarity":
            # Penalises missing tables that should have been there. But not if irrelevant tables were.
            # Binary average assumes that this score is aggregate with a sum.
            score = float(jaccard_score(y_pred=y_pred, y_true=y_true, average="binary"))
            return score

        return float(set(y_pred) == set(y_true))

    def table_match_factory(self, metric="hamming_loss") -> Callable:
        """Factory for function that scores the match between tables found in sql query, and ground truth
        expected tables for the query."""

        def func(user_query: str, sql_result: str) -> float:
            assert type(sql_result) == str, "type(sql_result) == str"
            assert type(user_query) == str, "type(user_query) == str"
            retrieved_tables = self.parse_table_names_from_sql(sql_result)
            return self.matching_tables(user_query, retrieved_tables, metric=metric)

        return func

    def table_match(
        self, user_query: str, sql_result: str, metric: str = "hamming_loss"
    ):

        retrieved_tables = self.parse_table_names_from_sql(sql_result)
        return self.matching_tables(user_query, retrieved_tables, metric=metric)

    @staticmethod
    def parse_table_names_from_sql(sql: str) -> Set[str]:
        """
        Extracts table names from the given SQL query and returns a set of unique table names.

        Args:
            sql (str): The SQL query from which to extract table names.

        Returns:
            Set[str]: A set containing unique table names extracted from the SQL query.
        """
        # TODO: unit tests - Some SQL languages might behave differently
        parsed = sqlparse.parse(sql)
        table_names = set()
        for stmt in parsed:
            for token in stmt.tokens:
                # Check if the token is an Identifier and likely a table name
                if (
                    isinstance(token, sqlparse.sql.Identifier)
                    and token.get_real_name().isidentifier()
                ):
                    table_names.add(token.get_real_name())

        return table_names

    def _qs_relevance(self, question: str, statement: str) -> str:
        # Borrowed from super().qs_relevance()
        return self.endpoint.run_me(
            lambda: self._create_chat_completion(
                prompt=str.format(
                    prompts.QS_RELEVANCE, question=question, statement=statement
                )
            )
        )

    def query_sql_relevance(self, question: str, statement: dict) -> float:
        """Judge the relevance of the example SQL-question pair, on the users input query"""
        json_sql_question = statement
        statement_str: str = (
            f"Another user asked a question: '{json_sql_question['question']}', and the SQL statement used to answer it was: '{json_sql_question['sql']}'"
        )

        llm_response = self._qs_relevance(question, statement_str)
        # Using rich for nicer printing
        rich.print(
            f"Running qs_relevance on inputs;"
            f":: question = [bold]{question}[/bold]"
            f":: statement = [bold]{statement_str}[/bold]\n"
            f"GPT judgement: '[bold]{llm_response}'[/bold]"
            f"score: [bold]{re_0_10_rating(llm_response)}[/bold]\n"
        )

        return re_0_10_rating(llm_response) / 10

    def qs_relevance(self, question: str, statement: str) -> float:
        """"""
        llm_response = self._qs_relevance(question, statement)
        # Using rich for nicer printing
        rich.print(
            f"Running qs_relevance on inputs;"
            f":: question = [bold]{question}[/bold]"
            f":: statement = [bold]{statement}[/bold]\n"
            f"GPT judgement: '[bold]{llm_response}'[/bold]"
            f"score: [bold]{re_0_10_rating(llm_response)}[/bold]\n"
        )

        return re_0_10_rating(llm_response) / 10


def _load_metrics(prompts: List[dict], config: dict) -> List[Feedback]:
    """Creates evaluation metrics for the TruLens recorder."""

    # A Evaluation model customised for sql table matching evaluation
    provider = StandAloneProvider(
        ground_truth_prompts=prompts,
        model_engine=config["evaluation"]["model"],
        possible_table_names=config["database"]["table_names"],
        dbpath=config["database"]["path"],
    )

    # How well the response agrees with the known to be true response.
    ground_truth_collection = GroundTruthAgreement(
        ground_truth=prompts, provider=provider
    )
    f_groundtruth_agreement_measure = Feedback(
        ground_truth_collection.agreement_measure, name="Agreement-to-truth measure"
    ).on_input_output()
    # Note: the above could have a newly synthesized response from a superior model in place of the ground truth;
    #   This is different to query-statement relevance. This takes the apps response to a query,
    #   and compares that response to a newly generated response to the same question. So, no ground
    #   truth data is used. Only checking whether the app performs similarly to another independent
    #   LLM. Useful to give confidence that the app is as-performant as an independent "SOTA model"

    # For evaluating each retrieved context
    f_qs_relevance_documentation = (
        Feedback(provider.qs_relevance, name="Query-Documentation Relevance")
        .on(
            question=Select.RecordCalls.get_related_documentation.args.question,
        )
        .on(statement=Select.RecordCalls.get_related_documentation.rets[:])
        .aggregate(np.mean)
    )
    f_qs_relevance_ddl = (
        Feedback(provider.qs_relevance, name="Query-DDL Relevance")
        .on(
            question=Select.RecordCalls.get_related_ddl.args.question,
        )
        .on(statement=Select.RecordCalls.get_related_ddl.rets[:])
        .aggregate(np.mean)
    )
    f_qs_relevance_sql = (
        Feedback(provider.query_sql_relevance, name="Query-SQL Relevance")
        .on(
            question=Select.RecordCalls.get_similar_question_sql.args.question,
        )
        .on(statement=Select.RecordCalls.get_similar_question_sql.rets[:])
        .aggregate(np.mean)
    )
    context_relevance_metrics = [
        f_qs_relevance_documentation,
        f_qs_relevance_ddl,
        f_qs_relevance_sql,
    ]

    # For checking if retrieved context is relevant to the response (sql queries, table schemas, DDL or documentation).
    # it looks for information overlap between retrieved documents, and the llms response.
    grounded = Groundedness(provider)
    f_groundedness_sql = (
        Feedback(grounded.groundedness_measure, name="groundedness_sql")
        .on(statement=Select.RecordCalls.get_similar_question_sql.rets[:])
        .on_output()
        .aggregate(grounded.grounded_statements_aggregator)
    )
    f_groundedness_ddl = (
        Feedback(grounded.groundedness_measure, name="groundedness_ddl")
        .on(Select.RecordCalls.get_related_ddl.rets[:])
        .on_output()
        .aggregate(grounded.grounded_statements_aggregator)
    )
    f_groundedness_document = (
        Feedback(grounded.groundedness_measure, name="groundedness_document")
        .on(Select.RecordCalls.get_related_documentation.rets[:])
        .on_output()
        .aggregate(grounded.grounded_statements_aggregator)
    )

    retrieval_metrics = []
    for metric in config["evaluation"]["retrieval"]["metrics"]:
        F = provider.table_match_factory(metric=metric)
        retrieval_metrics.append(
            Feedback(
                F, name=f"Matching Tables: {metric.replace('_', ' ').title()}"
            ).on_input_output()
        )

    # Note: some metrics use the LLM to perform the scoring. Consumes tokens / cost.
    return [
        f_groundtruth_agreement_measure,
        f_groundedness_ddl,
        f_groundedness_sql,
        f_groundedness_document,
        *context_relevance_metrics,
        *retrieval_metrics,
    ]


def init_vanna_training(vn: ChromaDB_VectorStore, config):
    """Adds context training examples to the vector store."""

    assert all(
        [
            vn.reomove_collection(collection_name=name)
            for name in ["sql", "ddl", "documentation"]
        ]
    )
    vn.connect_to_sqlite(config["database"]["path"])

    vn.train(
        sql="""SELECT FirstName from employees where FirstName LIKE 'A%';""",
        question="List the employees whos first name starts with 'A'",
    )
    vn.train(
        documentation="The 'employees' table contains the FirstName and LastName of employees"
    )
    vn.train(
        ddl="""(
        [EmployeeId] INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        [LastName] NVARCHAR(20)  NOT NULL,
        [FirstName] NVARCHAR(20)  NOT NULL,
        [Title] NVARCHAR(30),
        [ReportsTo] INTEGER,
        [BirthDate] DATETIME,
        [HireDate] DATETIME,
        FOREIGN KEY ([ReportsTo]) REFERENCES "employees" ([EmployeeId])
                    ON DELETE NO ACTION ON UPDATE NO ACTION)"""
    )


def run(vn: OllamaLocalDB, prompts: List[dict], config: dict, app_id=None):
    """creates metrics to evaluate the vanna pipeline, instruments the app with them, then runs some test prompts."""

    evaluation_metrics = _load_metrics(prompts, config)
    tru_recorder = TruCustomApp(
        vn,
        feedbacks=evaluation_metrics,
        tru=tru,
        app_id=app_id if app_id else f"{config['model']}",
    )

    for i, prompt in enumerate(prompts):
        response, record = tru_recorder.with_record(vn.generate_sql, prompt["query"])
        # manually add costs, since Ollama & Litellm served locally doesnt integrate cost & token counting
        record.cost.n_prompt_tokens = vn.call_log[i][1]["prompt_eval_count"]
        record.cost.n_completion_tokens = vn.call_log[i][1]["eval_count"]
        record.cost.n_tokens = (
            record.cost.n_completion_tokens + record.cost.n_prompt_tokens
        )
        record.cost.cost = 0.99  # Example cost of inference

        tru_recorder.tru.add_record(record)


if __name__ == "__main__":

    # Configures both the vanna app, and the evaluation pipeline
    config = {  # Vector store location
        "path": f"./_vectorstore/{date.today()}",
        "ollama_host": "http://localhost:11434",
        # Ollama must be initialised with models. Specify which one to use here
        "model": "mistralreranker",
        "database": {
            "path": "/mnt/c/Users/ssch7/repos/db-chat-assistant/data/chinook.db",
            # list all table names here, so response SQL calls can be checked against them.
            "table_names": ["employees", "artists", "customers"],
        },
        "evaluation": {
            "retrieval": {"metrics": ["hamming_loss"]},
            "model": "ollama/mistralreranker",
        },
    }

    # Evaluate the app with These prompts and their known ground truth answers.
    test_prompts = [
        dict(
            query="List the top twelve employees",
            sql="SELECT FirstName, LastName from employees LIMIT 12;",
            tables=["employees"],
            prompt="List the top twelve employees",
        ),
        dict(
            query="Who were the employees by first name, who served customers with first names starting with 'A'?",
            sql="""SELECT e.FirstName FROM employees e JOIN customers c ON e.EmployeeId = c.SupportRepId WHERE c.FirstName LIKE 'A%';""",
            tables=["employees", "customers"],
            prompt="Who were the employees by first name, who served customers with first names starting with 'A'?",
        ),
    ]

    # Note: Alternatively, download more test data from;
    # wget https://github.com/jkkummerfeld/text2sql-data/blob/master/data/restaurants.json
    # wget https://github.com/jkkummerfeld/text2sql-data/blob/master/data/restaurants-schema.csv

    vn = OllamaLocalDB(config=config)
    init_vanna_training(vn, config)
    run(vn, test_prompts, config, app_id="Mistral 7B : OllamaLocalDB")

    # Add a challenger app, that uses a different LLM
    config["model"] = "llama2reranker"
    vn = OllamaLocalDB(config=config)
    init_vanna_training(vn, config)
    run(vn, test_prompts, config, app_id="Llama2 7B : OllamaLocalDB")
