from .palm import Palm


def test_bison_model(temperature: float = 0.2) -> None:
    # params to use with Bison
    config = {
        "temperature": 0.7,  # Temperature controls the degree of randomness in token selection.
        "max_output_tokens": 256,  # Token limit determines the maximum amount of text output.
        "top_p": 0.96,  # Tokens are selected from most probable to least until the sum of their probabilities equals the top_p value.
        "top_k": 40,  # A top_k of 1 means the selected token is the most probable among all tokens.
        "model": "chat-bison@001",  # Which model to use, e.g., Bison
    }

    palm_client = Palm(
        client=None,
        config=config,
    )

    response = palm_client.generate_sql("How many chocolates are there?")

    print(f"Response from Model: {response.text}")

    return response


if __name__ == "__main__":
    test_bison_model()
