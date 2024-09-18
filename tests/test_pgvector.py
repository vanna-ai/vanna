import os

from dotenv import load_dotenv

from vanna.pgvector import PG_VectorStore

load_dotenv()


def get_vanna_connection_string():
    server = os.environ.get("PG_SERVER")
    driver = "psycopg"
    port = 5434
    database = os.environ.get("PG_DATABASE")
    username = os.environ.get("PG_USERNAME")
    password = os.environ.get("PG_PASSWORD")

    return f"postgresql+psycopg://{username}:{password}@{server}:{port}/{database}"


def test_pgvector():
    connection_string = get_vanna_connection_string()
    pgclient = PG_VectorStore(config={"connection_string": connection_string})
    assert pgclient is not None
