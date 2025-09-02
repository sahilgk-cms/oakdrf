import logging
import os
from oakdrf.config import LOGS_DIRECTORY


if not os.path.exists(LOGS_DIRECTORY):
    os.makedirs(LOGS_DIRECTORY)

LOG_FILE_PATH = os.path.join(LOGS_DIRECTORY, "oak_chatbot.log")


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    basic_formatter = logging.Formatter('%(asctime)s - %(filename)s - %(lineno)s - %(levelname)s: %(message)s')

    file_handler = logging.FileHandler(LOG_FILE_PATH, mode = "a")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(basic_formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(basic_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger
