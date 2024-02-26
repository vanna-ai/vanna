from vertexai.language_models import ChatModel

from vanna.chromadb.chromadb_vector import ChromaDB_VectorStore
from vanna.palm.palm import Palm


def test_bison_model():
    # params to use with Bison
    config = {
        "temperature": 0.7,  # Temperature controls the degree of randomness in token selection.
        "max_output_tokens": 256,  # Token limit determines the maximum amount of text output.
        "top_p": 0.96,  # Tokens are selected from most probable to least until the sum of their probabilities equals the top_p value.
        "top_k": 40,  # A top_k of 1 means the selected token is the most probable among all tokens.
        "model": "chat-bison@001",  # Which model to use, e.g., Bison
        "client": ChatModel("chat-bison@001"),
    }

    class MyVanna(ChromaDB_VectorStore, Palm):
        def __init__(self, config=None):
            ChromaDB_VectorStore.__init__(self, config=config)
            Palm.__init__(self, config=config)

    vn = MyVanna(config=config)

    response = vn.generate_sql("How many chocolates are there?")

    print(f"Response from Model: {response.text}")

    return response


if __name__ == "__main__":
    test_bison_model()
