import re


def sanitize_dataset_name(dataset_name):
    try:
        # Convert the dataset name to lowercase
        dataset_name = dataset_name.lower()

        # Replace spaces with a hyphen
        dataset_name = dataset_name.replace(" ", "-")

        # Remove or replace special characters with a hyphen
        dataset_name = re.sub(r"[^a-zA-Z0-9-]", "", dataset_name)

        # Remove multiple hyphens, if any
        dataset_name = re.sub(r"-+", "-", dataset_name)

        return dataset_name
    except Exception as e:
        raise e