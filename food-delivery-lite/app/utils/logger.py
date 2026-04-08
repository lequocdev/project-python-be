import logging
import sys
from app.config import settings


def get_logger(name: str) -> logging.Logger:
    """
    Trả về logger với structured format.
    Log level lấy từ settings.LOG_LEVEL (.env).
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger  # Tránh đăng ký handler nhiều lần

    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False

    return logger
