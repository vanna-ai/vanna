**ZhipuAI Language Models**
  
  **Table of Contents**
  
  - [ZhipuAI_Chat](#zhipuai_chat)
  - [ZhipuAI_Embeddings](#zhipuai_embeddings)
      - [ZhipuAIEmbeddingFunction](#zhipuaiembeddingfunction)
  

**ZhipuAI_Chat**

The `ZhipuAI_Chat` class provides an interface to interact with the ZhipuAI chat assistant API. This class makes it easy to send messages to the API and receive responses.

```python
from .ZhipuAI_Chat import ZhipuAI_Chat

# Create a new ZhipuAI_Chat object
chat = ZhipuAI_Chat()

# Send a message to the API
response = chat.send_message("Hello, ZhipuAI!")

# Print the response from the API
print(response)
```

**ZhipuAI_Embeddings**

The `ZhipuAI_Embeddings` class provides an interface to interact with the ZhipuAI embeddings API. This class makes it easy to generate embeddings for text data.

```python
from .ZhipuAI_Embeddings import ZhipuAI_Embeddings, ZhipuAIEmbeddingFunction

# Create a new ZhipuAI_Embeddings object
embeddings = ZhipuAI_Embeddings()

# Generate embeddings for a piece of text
embeddings = embeddings.generate_embeddings("Hello, world!")

# Print the embeddings
print(embeddings)
```

**ZhipuAIEmbeddingFunction**

The `ZhipuAIEmbeddingFunction` class is a helper class that can be used to generate embeddings for text data using a specific embedding function.

```python
from .ZhipuAI_Embeddings import ZhipuAIEmbeddingFunction

# Create a new ZhipuAIEmbeddingFunction object
embedding_function = ZhipuAIEmbeddingFunction("average")

# Generate embeddings for a piece of text
embeddings = embedding_function.generate_embeddings("Hello, world!")

# Print the embeddings
print(embeddings)
```