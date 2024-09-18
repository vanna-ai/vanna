from vanna.pgvector import PG_VectorStore


def test_pgvector():
    pgclient = PG_VectorStore(config={"connection_string": ""})
    assert pgclient is not None
