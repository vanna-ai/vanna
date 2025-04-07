import os

from vanna.anthropic.anthropic_chat import Anthropic_Chat
from vanna.cohere.cohere_chat import Cohere_Chat
from vanna.google import GoogleGeminiChat
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
# AZURE_SEARCH_API_KEY = os.environ['AZURE_SEARCH_API_KEY']

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

from vanna.qdrant import Qdrant_VectorStore


class VannaQdrant(Qdrant_VectorStore, OpenAI_Chat):
    def __init__(self, config=None):
        Qdrant_VectorStore.__init__(self, config=config)
        OpenAI_Chat.__init__(self, config=config)

from qdrant_client import QdrantClient

qdrant_memory_client = QdrantClient(":memory:")

vn_qdrant = VannaQdrant(config={'client': qdrant_memory_client, 'api_key': OPENAI_API_KEY, 'model': 'gpt-3.5-turbo'})
vn_qdrant.connect_to_sqlite('https://vanna.ai/Chinook.sqlite')

def test_vn_qdrant():
    df_ddl = vn_qdrant.run_sql("SELECT type, sql FROM sqlite_master WHERE sql is not null")

    for ddl in df_ddl['sql'].to_list():
        vn_qdrant.train(ddl=ddl)

    sql = vn_qdrant.generate_sql("What are the top 7 customers by sales?")
    df = vn_qdrant.run_sql(sql)
    assert len(df) == 7

from vanna.chromadb.chromadb_vector import ChromaDB_VectorStore
from vanna.openai.openai_chat import OpenAI_Chat


class MyVanna(ChromaDB_VectorStore, OpenAI_Chat):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        OpenAI_Chat.__init__(self, config=config)

vn_chroma = MyVanna(config={'api_key': OPENAI_API_KEY, 'model': 'gpt-3.5-turbo'})
vn_chroma.connect_to_sqlite('https://vanna.ai/Chinook.sqlite')

def test_vn_chroma():
    existing_training_data = vn_chroma.get_training_data()
    if len(existing_training_data) > 0:
        for _, training_data in existing_training_data.iterrows():
            vn_chroma.remove_training_data(training_data['id'])

    df_ddl = vn_chroma.run_sql("SELECT type, sql FROM sqlite_master WHERE sql is not null")

    for ddl in df_ddl['sql'].to_list():
        vn_chroma.train(ddl=ddl)

    sql = vn_chroma.generate_sql("What are the top 7 customers by sales?")
    df = vn_chroma.run_sql(sql)
    assert len(df) == 7

# from vanna.azuresearch.azuresearch_vector import AzureAISearch_VectorStore


# class VannaAzureSearch(AzureAISearch_VectorStore, OpenAI_Chat):
#     def __init__(self, config=None):
#         AzureAISearch_VectorStore.__init__(self, config=config)
#         OpenAI_Chat.__init__(self, config=config)

# vn_azure_search = VannaAzureSearch(config={'azure_search_api_key': AZURE_SEARCH_API_KEY,'api_key': OPENAI_API_KEY, 'model': 'gpt-3.5-turbo'})
# vn_azure_search.connect_to_sqlite('https://vanna.ai/Chinook.sqlite')

# def test_vn_azure_search():
#     existing_training_data = vn_azure_search.get_training_data()
#     print(existing_training_data)
#     if len(existing_training_data) > 0:
#         for _, training_data in existing_training_data.iterrows():
#             vn_azure_search.remove_training_data(training_data['id'])

#     df_ddl = vn_azure_search.run_sql("SELECT type, sql FROM sqlite_master WHERE sql is not null")
#     for ddl in df_ddl['sql'].to_list():
#         vn_azure_search.train(ddl=ddl)

#     sql = vn_azure_search.generate_sql("What are the top 7 customers by sales?")
#     df = vn_azure_search.run_sql(sql)
#     assert len(df) == 7

from vanna.milvus import Milvus_VectorStore


class VannaMilvus(Milvus_VectorStore, OpenAI_Chat):
    def __init__(self, config=None):
        Milvus_VectorStore.__init__(self, config=config)
        OpenAI_Chat.__init__(self, config=config)

vn_milvus = VannaMilvus(config={'api_key': OPENAI_API_KEY, 'model': 'gpt-3.5-turbo'})
vn_milvus.connect_to_sqlite('https://vanna.ai/Chinook.sqlite')

def test_vn_milvus():
    existing_training_data = vn_milvus.get_training_data()
    if len(existing_training_data) > 0:
        for _, training_data in existing_training_data.iterrows():
            vn_milvus.remove_training_data(training_data['id'])

    df_ddl = vn_milvus.run_sql("SELECT type, sql FROM sqlite_master WHERE sql is not null")

    for ddl in df_ddl['sql'].to_list():
        vn_milvus.train(ddl=ddl)

    sql = vn_milvus.generate_sql("What are the top 7 customers by sales?")
    df = vn_milvus.run_sql(sql)
    assert len(df) == 7


class VannaNumResults(ChromaDB_VectorStore, OpenAI_Chat):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        OpenAI_Chat.__init__(self, config=config)

vn_chroma_n_results = MyVanna(config={'api_key': OPENAI_API_KEY, 'model': 'gpt-3.5-turbo', 'n_results': 1})
vn_chroma_n_results_ddl = MyVanna(config={'api_key': OPENAI_API_KEY, 'model': 'gpt-3.5-turbo', 'n_results_ddl': 2})
vn_chroma_n_results_sql = MyVanna(config={'api_key': OPENAI_API_KEY, 'model': 'gpt-3.5-turbo', 'n_results_sql': 3})
vn_chroma_n_results_documentation = MyVanna(config={'api_key': OPENAI_API_KEY, 'model': 'gpt-3.5-turbo', 'n_results_documentation': 4})

def test_n_results():
    for i in range(1, 10):
        vn_chroma.train(question=f"What are the total sales for customer {i}?", sql=f"SELECT SUM(sales) FROM example_sales WHERE customer_id = {i}")

    for i in range(1, 10):
        vn_chroma.train(documentation=f"Sample documentation {i}")

    question = "Whare are the top 5 customers by sales?"
    assert len(vn_chroma_n_results.get_related_ddl(question)) == 1
    assert len(vn_chroma_n_results.get_related_documentation(question)) == 1
    assert len(vn_chroma_n_results.get_similar_question_sql(question)) == 1

    assert len(vn_chroma_n_results_ddl.get_related_ddl(question)) == 2
    assert len(vn_chroma_n_results_ddl.get_related_documentation(question)) != 2
    assert len(vn_chroma_n_results_ddl.get_similar_question_sql(question)) != 2

    assert len(vn_chroma_n_results_sql.get_related_ddl(question)) != 3
    assert len(vn_chroma_n_results_sql.get_related_documentation(question)) != 3
    assert len(vn_chroma_n_results_sql.get_similar_question_sql(question)) == 3

    assert len(vn_chroma_n_results_documentation.get_related_ddl(question)) != 4
    assert len(vn_chroma_n_results_documentation.get_related_documentation(question)) == 4
    assert len(vn_chroma_n_results_documentation.get_similar_question_sql(question)) != 4

class VannaClaude(VannaDB_VectorStore, Anthropic_Chat):
    def __init__(self, config=None):
        VannaDB_VectorStore.__init__(self, vanna_model=MY_VANNA_MODEL, vanna_api_key=MY_VANNA_API_KEY, config=config)
        Anthropic_Chat.__init__(self, config={'api_key': ANTHROPIC_API_KEY, 'model': ANTHROPIC_Model})


vn_claude = VannaClaude()
vn_claude.connect_to_sqlite('https://vanna.ai/Chinook.sqlite')


def test_vn_claude():
    sql = vn_claude.generate_sql("What are the top 8 customers by sales?")
    df = vn_claude.run_sql(sql)
    assert len(df) == 8

class VannaGemini(VannaDB_VectorStore, GoogleGeminiChat):
    def __init__(self, config=None):
        VannaDB_VectorStore.__init__(self, vanna_model=MY_VANNA_MODEL, vanna_api_key=MY_VANNA_API_KEY, config=config)
        GoogleGeminiChat.__init__(self, config=config)

vn_gemini = VannaGemini(config={'api_key': os.environ['GEMINI_API_KEY']})
vn_gemini.connect_to_sqlite('https://vanna.ai/Chinook.sqlite')

def test_vn_gemini():
    sql = vn_gemini.generate_sql("What are the top 9 customers by sales?")
    df = vn_gemini.run_sql(sql)
    assert len(df) == 9

class VannaCohere(VannaDB_VectorStore, Cohere_Chat):
    def __init__(self, config=None):
        VannaDB_VectorStore.__init__(self, vanna_model=MY_VANNA_MODEL, vanna_api_key=MY_VANNA_API_KEY, config=config)
        Cohere_Chat.__init__(self, config=config)

try:
    COHERE_API_KEY = os.environ['COHERE_API_KEY']
    vn_cohere = VannaCohere(config={'api_key': COHERE_API_KEY, 'model': 'command-a-03-2025'})
    vn_cohere.connect_to_sqlite('https://vanna.ai/Chinook.sqlite')
    
    def test_vn_cohere():
        sql = vn_cohere.generate_sql("What are the top 10 customers by sales?")
        df = vn_cohere.run_sql(sql)
        assert len(df) == 10
except KeyError:
    print("Skipping Cohere tests - COHERE_API_KEY not found in environment variables")

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
