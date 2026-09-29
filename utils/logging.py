import sys
import logging

ALLOWED_LOGGING_LEVELS = ['INFO', 'DEBUG', 'WARNING', 'ERROR']
DEFAULT_LEVEL = 'INFO'


def get_logging_level(log_level):
    assert log_level in ALLOWED_LOGGING_LEVELS, 'Your logging level is set incorrectly'

    if log_level == 'INFO':
        logging_log_level = logging.INFO
    elif log_level == 'DEBUG':
        logging_log_level = logging.DEBUG
    elif log_level == 'WARNING':
        logging_log_level = logging.WARNING
    elif log_level == 'ERROR':
        logging_log_level = logging.ERROR

    return logging_log_level


def get_logger(name, log_level='INFO'):
    logger = logging.getLogger(name)
    logging_log_level = get_logging_level(log_level)
    logger.setLevel(logging_log_level)


    if logger.hasHandlers():
        logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger