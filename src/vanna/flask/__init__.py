import logging
import uuid
from abc import ABC, abstractmethod
from functools import wraps

import flask
import requests
from flask import Flask, Response, jsonify, request

from .assets import css_content, html_content, js_content


class Cache(ABC):
    @abstractmethod
    def generate_id(self, *args, **kwargs):
        pass

    @abstractmethod
    def get(self, id, field):
        pass

    @abstractmethod
    def get_all(self, field_list) -> list:
        pass

    @abstractmethod
    def set(self, id, field, value):
        pass

    @abstractmethod
    def delete(self, id):
        pass


class MemoryCache(Cache):
    def __init__(self):
        self.cache = {}

    def generate_id(self, *args, **kwargs):
        return str(uuid.uuid4())

    def set(self, id, field, value):
        if id not in self.cache:
            self.cache[id] = {}

        self.cache[id][field] = value

    def get(self, id, field):
        if id not in self.cache:
            return None

        if field not in self.cache[id]:
            return None

        return self.cache[id][field]

    def get_all(self, field_list) -> list:
        return [
            {"id": id, **{field: self.get(id=id, field=field) for field in field_list}}
            for id in self.cache
        ]

    def delete(self, id):
        if id in self.cache:
            del self.cache[id]


class VannaFlaskApp:
    flask_app = None

    def requires_cache(self, fields):
        def decorator(f):
            @wraps(f)
            def decorated(*args, **kwargs):
                id = request.args.get("id")

                if id is None:
                    id = request.json.get("id")
                    if id is None:
                        return jsonify({"type": "error", "error": "No id provided"})

                for field in fields:
                    if self.cache.get(id=id, field=field) is None:
                        return jsonify({"type": "error", "error": f"No {field} found"})

                field_values = {
                    field: self.cache.get(id=id, field=field) for field in fields
                }

                # Add the id to the field_values
                field_values["id"] = id

                return f(*args, **field_values, **kwargs)

            return decorated

        return decorator

    def __init__(self, vn, cache: Cache = MemoryCache(),
                    allow_llm_to_see_data=False,
                    logo="https://img.vanna.ai/vanna-flask.svg",
                    title="Welcome to Vanna.AI",
                    subtitle="Your AI-powered copilot for SQL queries.",
                    show_training_data=True,
                    suggested_questions=True,
                    sql=True,
                    table=True,
                    csv_download=True,
                    chart=True,
                    redraw_chart=True,
                    auto_fix_sql=True,
                    ask_results_correct=True,
                    followup_questions=True,
                    summarization=True
                 ):
        """
        Expose a Flask app that can be used to interact with a Vanna instance.

        Args:
            vn: The Vanna instance to interact with.
            cache: The cache to use. Defaults to MemoryCache, which uses an in-memory cache. You can also pass in a custom cache that implements the Cache interface.
            allow_llm_to_see_data: Whether to allow the LLM to see data. Defaults to False.
            logo: The logo to display in the UI. Defaults to the Vanna logo.
            title: The title to display in the UI. Defaults to "Welcome to Vanna.AI".
            subtitle: The subtitle to display in the UI. Defaults to "Your AI-powered copilot for SQL queries.".
            show_training_data: Whether to show the training data in the UI. Defaults to True.
            suggested_questions: Whether to show suggested questions in the UI. Defaults to True.
            sql: Whether to show the SQL input in the UI. Defaults to True.
            table: Whether to show the table output in the UI. Defaults to True.
            csv_download: Whether to allow downloading the table output as a CSV file. Defaults to True.
            chart: Whether to show the chart output in the UI. Defaults to True.
            redraw_chart: Whether to allow redrawing the chart. Defaults to True.
            auto_fix_sql: Whether to allow auto-fixing SQL errors. Defaults to True.
            ask_results_correct: Whether to ask the user if the results are correct. Defaults to True.
            followup_questions: Whether to show followup questions. Defaults to True.
            summarization: Whether to show summarization. Defaults to True.

        Returns:
            None
        """
        self.flask_app = Flask(__name__)
        self.vn = vn
        self.cache = cache
        self.allow_llm_to_see_data = allow_llm_to_see_data
        self.logo = logo
        self.title = title
        self.subtitle = subtitle
        self.show_training_data = show_training_data
        self.suggested_questions = suggested_questions
        self.sql = sql
        self.table = table
        self.csv_download = csv_download
        self.chart = chart
        self.redraw_chart = redraw_chart
        self.auto_fix_sql = auto_fix_sql
        self.ask_results_correct = ask_results_correct
        self.followup_questions = followup_questions
        self.summarization = summarization

        log = logging.getLogger("werkzeug")
        log.setLevel(logging.ERROR)

        @self.flask_app.route("/api/v0/get_config", methods=["GET"])
        def get_config():
            return jsonify(
                {
                    "type": "config",
                    "config": {
                        "logo": self.logo,
                        "title": self.title,
                        "subtitle": self.subtitle,
                        "show_training_data": self.show_training_data,
                        "suggested_questions": self.suggested_questions,
                        "sql": self.sql,
                        "table": self.table,
                        "csv_download": self.csv_download,
                        "chart": self.chart,
                        "redraw_chart": self.redraw_chart,
                        "auto_fix_sql": self.auto_fix_sql,
                        "ask_results_correct": self.ask_results_correct,
                        "followup_questions": self.followup_questions,
                        "summarization": self.summarization,
                    },
                }
            )

        @self.flask_app.route("/api/v0/generate_questions", methods=["GET"])
        def generate_questions():
            # If self has an _model attribute and model=='chinook'
            if hasattr(self.vn, "_model") and self.vn._model == "chinook":
                return jsonify(
                    {
                        "type": "question_list",
                        "questions": [
                            "What are the top 10 artists by sales?",
                            "What are the total sales per year by country?",
                            "Who is the top selling artist in each genre? Show the sales numbers.",
                            "How do the employees rank in terms of sales performance?",
                            "Which 5 cities have the most customers?",
                        ],
                        "header": "Here are some questions you can ask:",
                    }
                )

            training_data = vn.get_training_data()

            # If training data is None or empty
            if training_data is None or len(training_data) == 0:
                return jsonify(
                    {
                        "type": "error",
                        "error": "No training data found. Please add some training data first.",
                    }
                )

            # Get the questions from the training data
            try:
                # Filter training data to only include questions where the question is not null
                questions = (
                    training_data[training_data["question"].notnull()]
                    .sample(5)["question"]
                    .tolist()
                )

                # Temporarily this will just return an empty list
                return jsonify(
                    {
                        "type": "question_list",
                        "questions": questions,
                        "header": "Here are some questions you can ask",
                    }
                )
            except Exception as e:
                return jsonify(
                    {
                        "type": "question_list",
                        "questions": [],
                        "header": "Go ahead and ask a question",
                    }
                )

        @self.flask_app.route("/api/v0/generate_sql", methods=["GET"])
        def generate_sql():
            question = flask.request.args.get("question")

            if question is None:
                return jsonify({"type": "error", "error": "No question provided"})

            id = self.cache.generate_id(question=question)
            sql = vn.generate_sql(question=question)

            self.cache.set(id=id, field="question", value=question)
            self.cache.set(id=id, field="sql", value=sql)

            return jsonify(
                {
                    "type": "sql",
                    "id": id,
                    "text": sql,
                }
            )

        @self.flask_app.route("/api/v0/run_sql", methods=["GET"])
        @self.requires_cache(["sql"])
        def run_sql(id: str, sql: str):
            try:
                if not vn.run_sql_is_set:
                    return jsonify(
                        {
                            "type": "error",
                            "error": "Please connect to a database using vn.connect_to_... in order to run SQL queries.",
                        }
                    )

                df = vn.run_sql(sql=sql)

                cache.set(id=id, field="df", value=df)

                return jsonify(
                    {
                        "type": "df",
                        "id": id,
                        "df": df.head(10).to_json(orient='records', date_format='iso'),
                    }
                )

            except Exception as e:
                return jsonify({"type": "sql_error", "error": str(e)})

        @self.flask_app.route("/api/v0/fix_sql", methods=["POST"])
        @self.requires_cache(["question", "sql"])
        def fix_sql(id: str, question:str, sql: str):
            error = flask.request.json.get("error")

            if error is None:
                return jsonify({"type": "error", "error": "No error provided"})

            question = f"I have an error: {error}\n\nHere is the SQL I tried to run: {sql}\n\nThis is the question I was trying to answer: {question}\n\nCan you rewrite the SQL to fix the error?"

            fixed_sql = vn.generate_sql(question=question)

            self.cache.set(id=id, field="sql", value=fixed_sql)

            return jsonify(
                {
                    "type": "sql",
                    "id": id,
                    "text": fixed_sql,
                }
            )


        @self.flask_app.route('/api/v0/update_sql', methods=['POST'])
        @self.requires_cache([])
        def update_sql(id: str):
            sql = flask.request.json.get('sql')

            if sql is None:
                return jsonify({"type": "error", "error": "No sql provided"})

            cache.set(id=id, field='sql', value=sql)

            return jsonify(
                {
                    "type": "sql",
                    "id": id,
                    "text": sql,
                })

        @self.flask_app.route("/api/v0/download_csv", methods=["GET"])
        @self.requires_cache(["df"])
        def download_csv(id: str, df):
            csv = df.to_csv()

            return Response(
                csv,
                mimetype="text/csv",
                headers={"Content-disposition": f"attachment; filename={id}.csv"},
            )

        @self.flask_app.route("/api/v0/generate_plotly_figure", methods=["GET"])
        @self.requires_cache(["df", "question", "sql"])
        def generate_plotly_figure(id: str, df, question, sql):
            chart_instructions = flask.request.args.get('chart_instructions')

            if chart_instructions is not None:
                question = f"{question}. When generating the chart, use these special instructions: {chart_instructions}"

            try:
                code = vn.generate_plotly_code(
                    question=question,
                    sql=sql,
                    df_metadata=f"Running df.dtypes gives:\n {df.dtypes}",
                )
                fig = vn.get_plotly_figure(plotly_code=code, df=df, dark_mode=False)
                fig_json = fig.to_json()

                cache.set(id=id, field="fig_json", value=fig_json)

                return jsonify(
                    {
                        "type": "plotly_figure",
                        "id": id,
                        "fig": fig_json,
                    }
                )
            except Exception as e:
                # Print the stack trace
                import traceback

                traceback.print_exc()

                return jsonify({"type": "error", "error": str(e)})

        @self.flask_app.route("/api/v0/get_training_data", methods=["GET"])
        def get_training_data():
            df = vn.get_training_data()

            if df is None or len(df) == 0:
                return jsonify(
                    {
                        "type": "error",
                        "error": "No training data found. Please add some training data first.",
                    }
                )

            return jsonify(
                {
                    "type": "df",
                    "id": "training_data",
                    "df": df.to_json(orient="records"),
                }
            )

        @self.flask_app.route("/api/v0/remove_training_data", methods=["POST"])
        def remove_training_data():
            # Get id from the JSON body
            id = flask.request.json.get("id")

            if id is None:
                return jsonify({"type": "error", "error": "No id provided"})

            if vn.remove_training_data(id=id):
                return jsonify({"success": True})
            else:
                return jsonify(
                    {"type": "error", "error": "Couldn't remove training data"}
                )

        @self.flask_app.route("/api/v0/train", methods=["POST"])
        def add_training_data():
            question = flask.request.json.get("question")
            sql = flask.request.json.get("sql")
            ddl = flask.request.json.get("ddl")
            documentation = flask.request.json.get("documentation")

            try:
                id = vn.train(
                    question=question, sql=sql, ddl=ddl, documentation=documentation
                )

                return jsonify({"id": id})
            except Exception as e:
                print("TRAINING ERROR", e)
                return jsonify({"type": "error", "error": str(e)})

        @self.flask_app.route("/api/v0/generate_followup_questions", methods=["GET"])
        @self.requires_cache(["df", "question", "sql"])
        def generate_followup_questions(id: str, df, question, sql):
            if self.allow_llm_to_see_data:
                followup_questions = vn.generate_followup_questions(
                    question=question, sql=sql, df=df
                )
                if followup_questions is not None and len(followup_questions) > 5:
                    followup_questions = followup_questions[:5]

                cache.set(id=id, field="followup_questions", value=followup_questions)

                return jsonify(
                    {
                        "type": "question_list",
                        "id": id,
                        "questions": followup_questions,
                        "header": "Here are some potential followup questions:",
                    }
                )
            else:
                cache.set(id=id, field="followup_questions", value=[])
                return jsonify(
                    {
                        "type": "question_list",
                        "id": id,
                        "questions": [],
                        "header": "Followup Questions can be enabled if you set allow_llm_to_see_data=True",
                    }
                )

        @self.flask_app.route("/api/v0/generate_summary", methods=["GET"])
        @self.requires_cache(["df", "question"])
        def generate_summary(id: str, df, question):
            if self.allow_llm_to_see_data:
                summary = vn.generate_summary(question=question, df=df)
                return jsonify(
                    {
                        "type": "text",
                        "id": id,
                        "text": summary,
                    }
                )
            else:
                return jsonify(
                    {
                        "type": "text",
                        "id": id,
                        "text": "Summarization can be enabled if you set allow_llm_to_see_data=True",
                    }
                )

        @self.flask_app.route("/api/v0/load_question", methods=["GET"])
        @self.requires_cache(
            ["question", "sql", "df", "fig_json"]
        )
        def load_question(id: str, question, sql, df, fig_json):
            try:
                return jsonify(
                    {
                        "type": "question_cache",
                        "id": id,
                        "question": question,
                        "sql": sql,
                        "df": df.head(10).to_json(orient="records"),
                        "fig": fig_json,
                    }
                )

            except Exception as e:
                return jsonify({"type": "error", "error": str(e)})

        @self.flask_app.route("/api/v0/get_question_history", methods=["GET"])
        def get_question_history():
            return jsonify(
                {
                    "type": "question_history",
                    "questions": cache.get_all(field_list=["question"]),
                }
            )

        @self.flask_app.route("/api/v0/<path:catch_all>", methods=["GET", "POST"])
        def catch_all(catch_all):
            return jsonify(
                {"type": "error", "error": "The rest of the API is not ported yet."}
            )

        @self.flask_app.route("/assets/<path:filename>")
        def proxy_assets(filename):
            if ".css" in filename:
                return Response(css_content, mimetype="text/css")

            if ".js" in filename:
                return Response(js_content, mimetype="text/javascript")

            # Return 404
            return "File not found", 404

        # Proxy the /vanna.svg file to the remote server
        @self.flask_app.route("/vanna.svg")
        def proxy_vanna_svg():
            remote_url = f"https://vanna.ai/img/vanna.svg"
            response = requests.get(remote_url, stream=True)

            # Check if the request to the remote URL was successful
            if response.status_code == 200:
                excluded_headers = [
                    "content-encoding",
                    "content-length",
                    "transfer-encoding",
                    "connection",
                ]
                headers = [
                    (name, value)
                    for (name, value) in response.raw.headers.items()
                    if name.lower() not in excluded_headers
                ]
                return Response(response.content, response.status_code, headers)
            else:
                return "Error fetching file from remote server", response.status_code

        @self.flask_app.route("/", defaults={"path": ""})
        @self.flask_app.route("/<path:path>")
        def hello(path: str):
            return html_content

    def run(self, *args, **kwargs):
        """
        Run the Flask app.

        Args:
            *args: Arguments to pass to Flask's run method.
            **kwargs: Keyword arguments to pass to Flask's run method.

        Returns:
            None
        """
        if args or kwargs:
            self.flask_app.run(*args, **kwargs)

        else:
            try:
                from google.colab import output

                output.serve_kernel_port_as_window(8084)
                from google.colab.output import eval_js

                print("Your app is running at:")
                print(eval_js("google.colab.kernel.proxyPort(8084)"))
            except:
                print("Your app is running at:")
                print("http://localhost:8084")

            self.flask_app.run(host="0.0.0.0", port=8084, debug=False)
