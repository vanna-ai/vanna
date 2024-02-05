import logging
import sys


def get_logger():
    """
    Method to get logger.

    Returns:
        logging: Logger
    """
    return logging.getLogger(__name__)


def initialize_logger():
    """
    Method that defines the standardization of logging.

    Returns:
        logging: Updated logger
    """
    logging.basicConfig(
        level=logging.INFO,  # default: 1
        format="[%(asctime)s] [%(filename)s:%(lineno)d] %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(stream=sys.stdout)],
    )

    return get_logger()


def setVerbosity(level: str = "INFO"):
    """
    Method that sets the logging level.

    Args:
        level (str): Which logging level to set. Defaults to "INFO". Supports the same values as the python logging class.
        Supported values are: "NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL".

    Returns:
        logging: Updated logger
    """

    return logging.getLogger().setLevel(level=level)
