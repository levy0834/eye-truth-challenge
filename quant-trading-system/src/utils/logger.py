"""
日志系统（简化版，使用标准库）
"""
import logging
import sys

def setup_logger(name: str = __name__, level: str = "INFO") -> logging.Logger:
    """设置日志"""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    if logger.handlers:
        return logger

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s - %(message)s",
        datefmt="%H:%M:%S"
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger
