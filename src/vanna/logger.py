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
