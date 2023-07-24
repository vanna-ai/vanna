import vanna as vn
import requests
import sys
import io
import pandas as pd

endpoint_base = 'https://debug.vanna.ai'

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

    datasets = vn.get_datasets()

    assert datasets == ['demo-tpc-h']

def test_create_dataset():
    rv = vn.create_dataset(dataset='test_org', db_type='Snowflake')
    assert rv == True

def test_is_user1_in_dataset():
    rv = vn.get_datasets()
    assert rv == ['demo-tpc-h', 'test_org']

def test_is_user2_in_dataset(monkeypatch):
    switch_to_user('user2', monkeypatch)

    datasets = vn.get_datasets()

    assert datasets == ['demo-tpc-h']

def test_switch_back_to_user1(monkeypatch):
    switch_to_user('user1', monkeypatch)

    datasets = vn.get_datasets()
    assert datasets == ['demo-tpc-h', 'test_org']

def test_set_dataset_my_dataset():
    try:
        vn.set_dataset('my-dataset')
        assert False
    except Exception as e:
        assert str(e) == "Please replace 'my-dataset' with the name of your dataset"

def test_set_dataset():
    vn.set_dataset('test_org')
    assert vn.__org == 'test_org' # type: ignore

def test_add_user_to_dataset(monkeypatch):
    rv = vn.add_user_to_dataset(dataset='test_org', email="user2@example.com", is_admin=False)
    assert rv == True

    switch_to_user('user2', monkeypatch)
    datasets = vn.get_datasets()
    assert datasets == ['demo-tpc-h', 'test_org']

def test_update_dataset_visibility(monkeypatch):
    rv = vn.update_dataset_visibility(public=True)
    # user2 is not an admin, so this should fail
    assert rv == False

    switch_to_user('user1', monkeypatch)
    rv = vn.update_dataset_visibility(public=True)

    switch_to_user('user3', monkeypatch)
    datasets = vn.get_datasets()
    assert datasets == ['demo-tpc-h', 'test_org']

    switch_to_user('user1', monkeypatch)

    rv = vn.update_dataset_visibility(public=False)
    assert rv == True

    switch_to_user('user3', monkeypatch)

    datasets = vn.get_datasets()
    assert datasets == ['demo-tpc-h']

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

    vn.set_dataset('demo-tpc-h')
    rv = vn.get_all_questions()
    assert rv.shape == (0, 0)

# def test_get_accuracy_stats():
#     rv = vn.get_accuracy_stats()
#     assert rv == AccuracyStats(num_questions=2, data={'No SQL Generated': 2, 'SQL Unable to Run': 0, 'Assumed Correct': 0, 'Flagged for Review': 0, 'Reviewed and Approved': 0, 'Reviewed and Rejected': 0, 'Reviewed and Updated': 0})

def test_add_documentation():
    rv = vn.add_documentation(documentation="This is the documentation")
    assert rv == True

def test_add_ddl():
    rv = vn.add_ddl(ddl="This is the ddl")
    assert rv == True

