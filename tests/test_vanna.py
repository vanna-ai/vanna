import vanna as vn
import requests
import sys
import io
import pandas as pd
import os
import pytest
from vanna.exceptions import ValidationError, ImproperlyConfigured

endpoint_base = os.environ.get('VANNA_ENDPOINT', 'https://debug.vanna.ai')

vn._endpoint = endpoint_base + '/rpc'
vn._unauthenticated_endpoint = endpoint_base + '/unauthenticated_rpc'

## Helper functions
def switch_to_user(user, monkeypatch):
    monkeypatch.setattr(sys, 'stdin', io.StringIO('DEBUG\n'))

    api_key = vn.get_api_key(email=f'{user}@example.com')
    vn.set_api_key(api_key)

## Tests

def test_debug_env():
    # Get endpoint_base + '/reset'
    r = requests.get(endpoint_base + '/reset')
    assert r.status_code == 200
    assert r.text == 'Database reset'

def test_create_user1(monkeypatch):
    monkeypatch.setattr(sys, 'stdin', io.StringIO('DEBUG\n'))

    api_key = vn.get_api_key(email='user1@example.com')
    vn.set_api_key(api_key)

    models = vn.get_models()

    assert models == ['demo-tpc-h']

def test_create_model():
    rv = vn.create_model(model='test_org', db_type='Snowflake')
    assert rv == True

def test_is_user1_in_model():
    rv = vn.get_models()
    assert rv == ['demo-tpc-h', 'test_org']

def test_is_user2_in_model(monkeypatch):
    switch_to_user('user2', monkeypatch)

    models = vn.get_models()

    assert models == ['demo-tpc-h']

def test_switch_back_to_user1(monkeypatch):
    switch_to_user('user1', monkeypatch)

    models = vn.get_models()
    assert models == ['demo-tpc-h', 'test_org']

def test_set_model_my_model():
    with pytest.raises(ValidationError):
        vn.set_model('my-model')

def test_set_model():
    vn.set_model('test_org')
    assert vn.__org == 'test_org' # type: ignore

def test_add_user_to_model(monkeypatch):
    rv = vn.add_user_to_model(model='test_org', email="user2@example.com", is_admin=False)
    assert rv == True

    switch_to_user('user2', monkeypatch)
    models = vn.get_models()
    assert models == ['demo-tpc-h', 'test_org']

def test_update_model_visibility(monkeypatch):
    rv = vn.update_model_visibility(public=True)
    # user2 is not an admin, so this should fail
    assert rv == False

    switch_to_user('user1', monkeypatch)
    rv = vn.update_model_visibility(public=True)

    switch_to_user('user3', monkeypatch)
    models = vn.get_models()
    assert models == ['demo-tpc-h', 'test_org']

    switch_to_user('user1', monkeypatch)

    rv = vn.update_model_visibility(public=False)
    assert rv == True

    switch_to_user('user3', monkeypatch)

    models = vn.get_models()
    assert models == ['demo-tpc-h']

def test_generate_explanation(monkeypatch):
    switch_to_user('user1', monkeypatch)
    rv = vn.generate_explanation(sql="SELECT * FROM students WHERE name = 'John Doe'")
    assert rv == 'AI Response'

def test_generate_question():
    rv = vn.generate_question(sql="SELECT * FROM students WHERE name = 'John Doe'")
    assert rv == 'AI Response'

def test_generate_sql():
    rv = vn.generate_sql(question="Who are the top 10 customers by Sales?")
    assert rv == 'No SELECT statement could be found in the SQL code'

def test_generate_plotly():
    data = {
    'Name': ['John', 'Emma', 'Tom', 'Emily', 'Alex'],
    'Age': [25, 28, 22, 31, 24],
    'Country': ['USA', 'Canada', 'UK', 'Australia', 'USA'],
    'Salary': [50000, 60000, 45000, 70000, 55000]
    }

    # Create a dataframe from the dictionary
    df = pd.DataFrame(data)

    rv = vn.generate_plotly_code(question="Who are the top 10 customers by Sales?", sql="SELECT * FROM students WHERE name = 'John Doe'", df=df)
    assert rv == 'AI Response'

def test_generate_questions():
    rv = vn.generate_questions()
    assert rv == ['AI Response']

def test_generate_followup_questions():
    data = {
    'Name': ['John', 'Emma', 'Tom', 'Emily', 'Alex'],
    'Age': [25, 28, 22, 31, 24],
    'Country': ['USA', 'Canada', 'UK', 'Australia', 'USA'],
    'Salary': [50000, 60000, 45000, 70000, 55000]
    }

    # Create a dataframe from the dictionary
    df = pd.DataFrame(data)

    questions = vn.generate_followup_questions(question="Who are the top 10 customers by Sales?", df=df)

    assert questions == ['AI Response']

def test_add_sql():
    rv = vn.add_sql(question="What's the data about student John Doe?", sql="SELECT * FROM students WHERE name = 'John Doe'")
    assert rv == True

    rv = vn.add_sql(question="What's the data about student Jane Doe?", sql="SELECT * FROM students WHERE name = 'Jane Doe'")
    assert rv == True

def test_generate_sql_caching():
    rv = vn.generate_sql(question="What's the data about student John Doe?")

    assert rv == 'SELECT * FROM students WHERE name = \'John Doe\''

def test_remove_sql():
    rv = vn.remove_sql(question="What's the data about student John Doe?")
    assert rv == True

def test_flag_sql():
    rv = vn.flag_sql_for_review(question="What's the data about student Jane Doe?")
    assert rv == True

def test_get_all_questions():
    rv = vn.get_all_questions()
    assert rv.shape == (3, 5)

    vn.set_model('demo-tpc-h')
    rv = vn.get_all_questions()
    assert rv.shape == (0, 0)

# def test_get_accuracy_stats():
#     rv = vn.get_accuracy_stats()
#     assert rv == AccuracyStats(num_questions=2, data={'No SQL Generated': 2, 'SQL Unable to Run': 0, 'Assumed Correct': 0, 'Flagged for Review': 0, 'Reviewed and Approved': 0, 'Reviewed and Rejected': 0, 'Reviewed and Updated': 0})

def test_add_documentation_fail():
    rv = vn.add_documentation(documentation="This is the documentation")
    assert rv == False

def test_add_ddl_pass_fail():
    rv = vn.add_ddl(ddl="This is the ddl")
    assert rv == False

def test_add_sql_pass_fail():
    rv = vn.add_sql(question="How many students are there?", sql="SELECT * FROM students")
    assert rv == False

def test_add_documentation_pass(monkeypatch):
    switch_to_user('user1', monkeypatch)
    vn.set_model('test_org')
    rv = vn.add_documentation(documentation="This is the documentation")
    assert rv == True

def test_add_ddl_pass():
    rv = vn.add_ddl(ddl="This is the ddl")
    assert rv == True

def test_add_sql_pass():
    rv = vn.add_sql(question="How many students are there?", sql="SELECT * FROM students")
    assert rv == True

num_training_data = 4

def test_get_training_data():
    rv = vn.get_training_data()
    assert rv.shape == (num_training_data, 4)

def test_remove_training_data():
    training_data = vn.get_training_data()

    for index, row in training_data.iterrows():
        rv = vn.remove_training_data(row['id'])
        assert rv == True

        assert vn.get_training_data().shape[0] == num_training_data-1-index

def test_create_model_and_add_user():
    created = vn.create_model('test_org2', 'Snowflake')
    assert created == True

    added = vn.add_user_to_model(model='test_org2', email="user5@example.com", is_admin=False)
    assert added == True

def test_ask_no_output():
    vn.run_sql = lambda sql: pd.DataFrame({'Name': ['John', 'Emma', 'Tom', 'Emily', 'Alex']})
    vn.generate_sql = lambda question: 'SELECT * FROM students'
    vn.ask(question="How many students are there?")

def test_ask_with_output():
    sql, df, fig, followup_questions = vn.ask(question="How many students are there?", print_results=False)

    assert sql == 'SELECT * FROM students'

    assert df.to_csv() == ',Name\n0,John\n1,Emma\n2,Tom\n3,Emily\n4,Alex\n'

def test_generate_meta():
    meta = vn.generate_meta("What tables are available?")

    assert meta == 'AI Response'

def test_double_train():
    vn.set_model('test_org')

    training_data = vn.get_training_data()
    assert training_data.shape == (0, 0)

    trained = vn.train(question="What's the data about student John Doe?", sql="SELECT * FROM students WHERE name = 'John Doe'")
    assert trained == True

    training_data = vn.get_training_data()
    assert training_data.shape == (1, 4)

    vn.train(question="What's the data about student John Doe?", sql="SELECT * FROM students WHERE name = 'John Doe'")

    training_data = vn.get_training_data()
    assert training_data.shape == (1, 4)

@pytest.mark.parametrize("sql_file_path, json_file_path, should_work", [
    ('tests/test_files/sql/testSqlSelect.sql', 'tests/test_files/training/questions.json', True),
    ('tests/test_files/sql/testSqlCreate.sql', 'tests/test_files/training/questions.json', True),
    ('tests/test_files/sql/testSql.sql', 'tests/test_files/training/s.json', False),
])
def test_train(sql_file_path, json_file_path, should_work):
    # if just question not sql
    with pytest.raises(ValidationError):
        vn.train(question="What's the data about student John Doe?")

    # if just sql
    assert vn.train(sql="SELECT * FROM students WHERE name = 'Jane Doe'") == True

    # if just sql and documentation=True
    assert vn.train(sql="SELECT * FROM students WHERE name = 'Jane Doe'", documentation=True) == True

    # if just ddl statement
    assert vn.train(ddl="This is the ddl") == True

    # if just sql_file
    if should_work:
        assert vn.train(sql_file=sql_file_path) == True
        assert vn.train(json_file=json_file_path) == True
    else:
        with pytest.raises(ImproperlyConfigured):
            vn.train(sql_file=sql_file_path)
            vn.train(json_file=json_file_path)
