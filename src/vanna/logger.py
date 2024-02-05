import logging
import sys


def get_logger():
    return logging.getLogger(__name__)


def initialize_logger():
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] [%(filename)s:%(lineno)d] %(levelname)s - %(message)s",
        handlers=logging.StreamHandler(stream=sys.stdout)
    )

    return get_logger()
