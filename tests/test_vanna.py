from vanna.openai.openai_chat import OpenAI_Chat
from vanna.vannadb.vannadb_vector import VannaDB_VectorStore
from vanna.mistral.mistral import Mistral
from vanna.remote import VannaDefault


import os

try:
    print("Trying to load .env")
    from dotenv import load_dotenv
    load_dotenv()
except Exception as e:
    print(f"Failed to load .env {e}")
    pass

MY_VANNA_MODEL = 'chinook'
MY_VANNA_API_KEY = os.environ['VANNA_API_KEY']
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
MISTRAL_API_KEY = os.environ['MISTRAL_API_KEY']

class VannaOpenAI(VannaDB_VectorStore, OpenAI_Chat):
    def __init__(self, config=None):
        VannaDB_VectorStore.__init__(self, vanna_model=MY_VANNA_MODEL, vanna_api_key=MY_VANNA_API_KEY, config=config)
        OpenAI_Chat.__init__(self, config=config)

vn_openai = VannaOpenAI(config={'api_key': OPENAI_API_KEY, 'model': 'gpt-3.5-turbo'})
vn_openai.connect_to_sqlite('https://vanna.ai/Chinook.sqlite')

def test_vn_openai():
    sql = vn_openai.generate_sql("What are the top 4 customers by sales?")
    df = vn_openai.run_sql(sql)
    assert len(df) == 4

class VannaMistral(VannaDB_VectorStore, Mistral):
    def __init__(self, config=None):
        VannaDB_VectorStore.__init__(self, vanna_model=MY_VANNA_MODEL, vanna_api_key=MY_VANNA_API_KEY, config=config)
        Mistral.__init__(self, config={'api_key': MISTRAL_API_KEY, 'model': 'mistral-tiny'})

vn_mistral = VannaMistral()
vn_mistral.connect_to_sqlite('https://vanna.ai/Chinook.sqlite')

def test_vn_mistral():
    sql = vn_mistral.generate_sql("What are the top 5 customers by sales?")
    df = vn_mistral.run_sql(sql)
    assert len(df) == 5

vn_default = VannaDefault(model=MY_VANNA_MODEL, api_key=MY_VANNA_API_KEY)
vn_default.connect_to_sqlite('https://vanna.ai/Chinook.sqlite')

def test_vn_default():
    sql = vn_default.generate_sql("What are the top 6 customers by sales?")
    df = vn_default.run_sql(sql)
    assert len(df) == 6