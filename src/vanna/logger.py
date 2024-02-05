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


def set_log_level(level: int = 1):
    """
    Method that sets the logging level.

    Args:
        level (int): Which logging level to set. Set 0 for Ignore, 1 for Info, 2 for Debug, and 3 for Error.

    Returns:
        logging: Updated logger
    """

    return logging.getLogger().setLevel(level=level)
