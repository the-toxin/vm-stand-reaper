import logging
import os
import sys
from enum import StrEnum
from typing import Optional

from vm_stand_reaper.adapters.environment_variables import EnvironmentVariableName


class LogLevel(StrEnum):
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"
    NOTSET = "NOTSET"


def setup_logging(
    level: Optional[str] = None,
    format: Optional[str] = None,
    datefmt: Optional[str] = None,
) -> None:
    """
    Setup basic logging.

    Args:
        level (LogLevel | None): Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
            If not provided, uses environment variable.
            If environment variable value is incorrect, it will be set to 'INFO.
        format (str | None): Custom format string for logs
        datefmt (str | None): Custom datefmt string for logs
    """
    if level is None:
        level = os.getenv(EnvironmentVariableName.LOG_LEVEL, LogLevel.NOTSET)
    if (level not in LogLevel) or (level == LogLevel.NOTSET):
        level = LogLevel.INFO
    if format is None:
        format = "[%(asctime)s] %(levelname)-8s [%(name)s:%(funcName)s:%(lineno)d] %(message)s"
    if datefmt is None:
        datefmt = "%Y-%m-%dT%H:%M:%SZ"

    logging.basicConfig(level=level, format=format, datefmt=datefmt, stream=sys.stderr)
