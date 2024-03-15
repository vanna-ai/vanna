from vertexai.language_models import ChatModel

from vanna.chromadb.chromadb_vector import ChromaDB_VectorStore
from vanna.palm.palm import Palm


def test_bison_model():

    class MyVanna(ChromaDB_VectorStore, Palm):
        def __init__(self, config=None):
            ChromaDB_VectorStore.__init__(self, config=config)
            Palm.__init__(self, client=ChatModel("chat-bison@001"), config=config)

    vn = MyVanna()

    response = vn.generate_sql("How many chocolates are there?")
    print(f"Response from Model: {response.text}")

    return response


if __name__ == "__main__":
    test_bison_model()
