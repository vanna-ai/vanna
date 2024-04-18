## Vanna Flask App

**Table of Contents:**

- [Introduction](#introduction)
- [Installation](#installation)
- [Usage](#usage)
    - [Initialization](#initialization)
    - [Available Routes](#available-routes)
- [Configuration](#configuration)
- [Auth](#auth)
- [Cache](#cache)
- [Security](#security)
- [Example](#example)

## Introduction

Vanna Flask App is a Flask-based application that allows you to interact with a Vanna instance. Vanna is an AI-powered copilot for SQL queries. With Vanna Flask App, you can generate SQL queries, run them, and visualize the results. You can also train Vanna on your own data.

## Installation

To install Vanna Flask App, run the following command:

```
pip install vanna-flask
```

## Usage

### Initialization

To initialize a Vanna Flask app, create an instance of the `VannaFlaskApp` class:

```python
from vanna_flask import VannaFlaskApp

# Create a Vanna instance
vn = Vanna()

# Create a Vanna Flask app
app = VannaFlaskApp(vn)
```

### Available Routes

The following routes are available in Vanna Flask App:

| Route | Method | Description |
|---|---|---|
| /auth/login | POST | Login |
| /auth/callback | GET | Callback after login |
| /auth/logout | GET | Logout |
| /api/v0/get_config | GET | Get the configuration of the app |
| /api/v0/generate_questions | GET | Generate questions |
| /api/v0/generate_sql | GET | Generate SQL |
| /api/v0/run_sql | GET | Run SQL |
| /api/v0/fix_sql | POST | Fix SQL |
| /api/v0/download_csv | GET | Download the results of a SQL query as a CSV file |
| /api/v0/generate_plotly_figure | GET | Generate a Plotly figure |
| /api/v0/get_training_data | GET | Get the training data |
| /api/v0/remove_training_data | POST | Remove training data |
| /api/v0/train | POST | Train Vanna |
| /api/v0/generate_followup_questions | GET | Generate followup questions |
| /api/v0/generate_summary | GET | Generate a summary of the results of a SQL query |
| /api/v0/load_question | GET | Load a question from the cache |
| /api/v0/get_question_history | GET | Get the question history |

## Configuration

The following configuration options are available in Vanna Flask App:

| Option | Default Value | Description |
|---|---|---|
| allow_llm_to_see_data | False | Whether to allow the LLM to see data |
| logo | https://img.vanna.ai/vanna-flask.svg | The logo to display in the UI |
| title | Welcome to Vanna.AI | The title to display in the UI |
| subtitle | Your AI-powered copilot for SQL queries. | The subtitle to display in the UI |
| show_training_data | True | Whether to show the training data in the UI |
| suggested_questions | True | Whether to show suggested questions in the UI |
| sql | True | Whether to show the SQL input in the UI |
| table | True | Whether to show the table output in the UI |
| csv_download | True | Whether to allow downloading the table output as a CSV file |
| chart | True | Whether to show the chart output in the UI |
| redraw_chart | True | Whether to allow redrawing the chart |
| auto_fix_sql | True | Whether to allow auto-fixing SQL errors |
| ask_results_correct | True | Whether to ask the user if the results are correct |
| followup_questions | True | Whether to show followup questions |
| summarization | True | Whether to show summarization |

## Auth

Vanna Flask App supports authentication using the `AuthInterface` interface. You can implement your own authentication method by creating a class that implements the `AuthInterface` interface.

To use your own authentication method, pass it to the `VannaFlaskApp` constructor:

```python
from vanna_flask import VannaFlaskApp
from my_auth import MyAuth

# Create a Vanna instance
vn = Vanna()

# Create a MyAuth instance
auth = MyAuth()

# Create a Vanna Flask app
app = VannaFlaskApp(vn, auth=auth)
```

## Cache

Vanna Flask App uses a cache to store data. The cache is implemented using the `Cache` interface. You can implement your own cache by creating a class that implements the `Cache` interface.

To use your own cache, pass it to the `VannaFlaskApp` constructor:

```python
from vanna_flask import VannaFlaskApp
from my_cache import MyCache

# Create a Vanna instance
vn = Vanna()

# Create a MyCache instance
cache = MyCache()

# Create a Vanna Flask app
app = VannaFlaskApp(vn, cache=cache)
```

## Security

Vanna Flask App uses the following security measures:

- **HTTPS:** All traffic is encrypted using HTTPS.
- **CSRF protection:** All forms are protected against CSRF attacks.
- **XSS protection:** All output is escaped to prevent XSS attacks.

## Example

The following code shows how to use Vanna Flask App:

```python
from vanna_flask import VannaFlaskApp

# Create a Vanna instance
vn = Vanna()

# Create a Vanna Flask app
app = VannaFlaskApp(vn)

# Run the app
app.run()
```

## Conclusion

Vanna Flask App is a powerful tool for interacting with Vanna. With Vanna Flask App, you can easily generate SQL queries, run them, and visualize the results. You can also train Vanna on your own data.