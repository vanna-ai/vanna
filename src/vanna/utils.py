import hashlib
import os
import re
import uuid
from typing import Union
from .exceptions import ImproperlyConfigured, ValidationError

def validate_config_path(path):
    """
    Validates the given configuration file path.
    This function checks if the provided path exists, is a file, and is readable.
    If any of these conditions are not met, it raises an ImproperlyConfigured exception.
    Args:
        path (str): The path to the configuration file.
    Raises:
        ImproperlyConfigured: If the path does not exist, is not a file, or is not readable.
    """
    if not os.path.exists(path):
        raise ImproperlyConfigured(
            f'No such configuration file: {path}'
        )

    if not os.path.isfile(path):
        raise ImproperlyConfigured(
            f'Config should be a file: {path}'
        )

    if not os.access(path, os.R_OK):
        raise ImproperlyConfigured(
            f'Cannot read the config file. Please grant read privileges: {path}'
        )


def sanitize_model_name(model_name):
    """
    Sanitizes the given model name by performing the following operations:
    - Converts the model name to lowercase.
    - Replaces spaces with hyphens.
    - Replaces multiple consecutive hyphens with a single hyphen.
    - Replaces underscores with hyphens if both underscores and hyphens are present.
    - Removes special characters, allowing only alphanumeric characters, hyphens, and underscores.
    - Removes hyphens or underscores from the beginning or end of the model name.
    Args:
        model_name (str): The model name to sanitize.
    Returns:
        str: The sanitized model name.
    Raises:
        ValidationError: If an error occurs during sanitization.
    """
    try:
        model_name = model_name.lower()

        # Replace spaces with a hyphen
        model_name = model_name.replace(" ", "-")

        if '-' in model_name:

            # remove double hyphones
            model_name = re.sub(r"-+", "-", model_name)
            if '_' in model_name:
                # If name contains both underscores and hyphen replace all underscores with hyphens
                model_name = re.sub(r'_', '-', model_name)

        # Remove special characters only allow underscore
        model_name = re.sub(r"[^a-zA-Z0-9-_]", "", model_name)

        # Remove hyphen or underscore if any at the last or first
        if model_name[-1] in ("-", "_"):
            model_name = model_name[:-1]
        if model_name[0] in ("-", "_"):
            model_name = model_name[1:]

        return model_name
    except Exception as e:
        raise ValidationError(e)


def deterministic_uuid(content: Union[str, bytes]) -> str:
    """Creates deterministic UUID on hash value of string or byte content.

    Args:
        content: String or byte representation of data.

    Returns:
        UUID of the content.
    """
    if isinstance(content, str):
        content_bytes = content.encode("utf-8")
    elif isinstance(content, bytes):
        content_bytes = content
    else:
        raise ValueError(f"Content type {type(content)} not supported !")

    hash_object = hashlib.sha256(content_bytes)
    hash_hex = hash_object.hexdigest()
    namespace = uuid.UUID("00000000-0000-0000-0000-000000000000")
    content_uuid = str(uuid.uuid5(namespace, hash_hex))

    return content_uuid
