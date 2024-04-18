## ChromaDB_VectorStore ✨

A vector store for ChromaDB.

### Table of Contents

- [Overview](#overview)
- [Usage](#usage)
- [Implementation Details](#implementation-details)

### Overview

This store allows you to store and retrieve vectors in ChromaDB. Vectors can be used for a variety of purposes, such as:

- Search
- Recommendation
- Classification

### Usage

To use this store, you will need to create a `ChromaDB_VectorStore` object. You can do this by passing a `ChromaDB` object to the constructor.

```python
from chromadb_vector import ChromaDB_VectorStore

vector_store = ChromaDB_VectorStore(chromadb)
```

Once you have created a `ChromaDB_VectorStore` object, you can use it to store and retrieve vectors. To store a vector, you will need to use the `put` method. The `put` method takes two arguments: a key and a vector.

```python
vector_store.put("my-key", [1, 2, 3])
```

To retrieve a vector, you will need to use the `get` method. The `get` method takes one argument: a key.

```python
vector = vector_store.get("my-key")
```

### Implementation Details

The `ChromaDB_VectorStore` class uses a B-tree to store vectors. The B-tree is a balanced search tree that is optimized for storing and retrieving data.

The `ChromaDB_VectorStore` class also uses a cache to improve performance. The cache is a temporary storage area that stores frequently accessed vectors. When a vector is requested, the cache is checked first to see if the vector is already stored in the cache. If the vector is not in the cache, it is loaded from the B-tree.

### Example Usage

The following code shows how to use the `ChromaDB_VectorStore` class to store and retrieve vectors.

```python
from chromadb_vector import ChromaDB_VectorStore

# Create a ChromaDB object
chromadb = ChromaDB()

# Create a ChromaDB_VectorStore object
vector_store = ChromaDB_VectorStore(chromadb)

# Store a vector
vector_store.put("my-key", [1, 2, 3])

# Retrieve a vector
vector = vector_store.get("my-key")
```