## 📝 Table of Contents

- [Introduction](#introduction)
- [Class: VannaBase](#class-vannabase)

## 📚 Introduction

This module provides a base class for vanna models.

## 🐍 Class: VannaBase

```python
from .base import VannaBase
```

The `VannaBase` class is a base class for vanna models. It provides the following functionality:

- A constructor that takes a `model` and a `name` as arguments.
- A `fit` method that fits the model to the data.
- A `predict` method that predicts the model's output for a given input.
- A `save` method that saves the model to a file.
- A `load` method that loads the model from a file.

### Example Usage

```python
import vanna

# Create a vanna model.
model = vanna.VannaBase(model, name="my_model")

# Fit the model to the data.
model.fit(data)

# Predict the model's output for a given input.
predictions = model.predict(input)

# Save the model to a file.
model.save("my_model.pkl")

# Load the model from a file.
model = vanna.VannaBase.load("my_model.pkl")
```