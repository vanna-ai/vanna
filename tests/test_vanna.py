import os

from vanna.anthropic.anthropic_chat import Anthropic_Chat
from vanna.mistral.mistral import Mistral
from vanna.openai.openai_chat import OpenAI_Chat
from vanna.remote import VannaDefault
from vanna.vannadb.vannadb_vector import VannaDB_VectorStore

try:
    print("Trying to load .env")
    from dotenv import load_dotenv
    load_dotenv()
except Exception as e:
    print(f"Failed to load .env {e}")
    pass

MY_VANNA_MODEL = 'chinook'
ANTHROPIC_Model = 'claude-3-sonnet-20240229'
MY_VANNA_API_KEY = os.environ['VANNA_API_KEY']
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
MISTRAL_API_KEY = os.environ['MISTRAL_API_KEY']
ANTHROPIC_API_KEY = os.environ['ANTHROPIC_API_KEY']
SNOWFLAKE_ACCOUNT = os.environ['SNOWFLAKE_ACCOUNT']
SNOWFLAKE_USERNAME = os.environ['SNOWFLAKE_USERNAME']
SNOWFLAKE_PASSWORD = os.environ['SNOWFLAKE_PASSWORD']

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

from vanna.chromadb.chromadb_vector import ChromaDB_VectorStore
from vanna.openai.openai_chat import OpenAI_Chat


class MyVanna(ChromaDB_VectorStore, OpenAI_Chat):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        OpenAI_Chat.__init__(self, config=config)

vn_chroma = MyVanna(config={'api_key': OPENAI_API_KEY, 'model': 'gpt-3.5-turbo'})
vn_chroma.connect_to_sqlite('https://vanna.ai/Chinook.sqlite')

def test_vn_chroma():
    df_ddl = vn_chroma.run_sql("SELECT type, sql FROM sqlite_master WHERE sql is not null")

    for ddl in df_ddl['sql'].to_list():
        vn_chroma.train(ddl=ddl)

    sql = vn_chroma.generate_sql("What are the top 7 customers by sales?")
    df = vn_chroma.run_sql(sql)
    assert len(df) == 7


class VannaClaude(VannaDB_VectorStore, Anthropic_Chat):
    def __init__(self, config=None):
        VannaDB_VectorStore.__init__(self, vanna_model=MY_VANNA_MODEL, vanna_api_key=MY_VANNA_API_KEY, config=config)
        Anthropic_Chat.__init__(self, config={'api_key': ANTHROPIC_API_KEY, 'model': ANTHROPIC_Model})


vn_claude = VannaClaude()
vn_claude.connect_to_sqlite('https://vanna.ai/Chinook.sqlite')


def test_vn_claude():
    sql = vn_claude.generate_sql("What are the top 5 customers by sales?")
    df = vn_claude.run_sql(sql)
    assert len(df) == 5

def test_training_plan():
    vn_dummy = VannaDefault(model=MY_VANNA_MODEL, api_key=MY_VANNA_API_KEY)

    vn_dummy.connect_to_snowflake(
        account=SNOWFLAKE_ACCOUNT,
        username=SNOWFLAKE_USERNAME,
        password=SNOWFLAKE_PASSWORD,
        database='SNOWFLAKE_SAMPLE_DATA',
    )

    df_information_schema = vn_dummy.run_sql("SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE table_schema = 'TPCH_SF1' ")

    plan = vn_dummy.get_training_plan_generic(df_information_schema)
    assert len(plan._plan) == 8
