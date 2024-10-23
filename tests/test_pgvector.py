import os

from dotenv import load_dotenv

# from vanna.pgvector import PG_VectorStore
# from vanna.openai import OpenAI_Chat

# assume .env file placed next to file with provided env vars
load_dotenv()

# def get_vanna_connection_string():
#     server = os.environ.get("PG_SERVER")
#     driver = "psycopg"
#     port = os.environ.get("PG_PORT", 5432)
#     database = os.environ.get("PG_DATABASE")
#     username = os.environ.get("PG_USERNAME")
#     password = os.environ.get("PG_PASSWORD")

# def test_pgvector_e2e():
#     # configure Vanna to use OpenAI and PGVector
#     class VannaCustom(PG_VectorStore, OpenAI_Chat):
#         def __init__(self, config=None):
#             PG_VectorStore.__init__(self, config=config)
#             OpenAI_Chat.__init__(self, config=config)
    
#     vn = VannaCustom(config={
#         'api_key': os.environ['OPENAI_API_KEY'],
#         'model': 'gpt-3.5-turbo',
#         "connection_string": get_vanna_connection_string(),
#     })

#     # connect to SQLite database
#     vn.connect_to_sqlite('https://vanna.ai/Chinook.sqlite')

#     # train Vanna on DDLs
#     df_ddl = vn.run_sql("SELECT type, sql FROM sqlite_master WHERE sql is not null")
#     for ddl in df_ddl['sql'].to_list():
#         vn.train(ddl=ddl)
#     assert len(vn.get_related_ddl("dummy question")) == 10  # assume 10 DDL chunks are retrieved by default
    
#     question = "What are the top 7 customers by sales?"
#     sql = vn.generate_sql(question)
#     df = vn.run_sql(sql)
#     assert len(df) == 7

#     # test if Vanna can generate an answer
#     answer = vn.ask(question)
#     assert answer is not None

