import logging
import sys
from collections.abc import Iterable

from loguru import logger

from app.core.config import settings


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame = logging.currentframe()
        depth = 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging() -> None:
    logger.remove()
    logger.add(
        sys.stderr,
        level=settings.LOG_LEVEL.upper(),
        backtrace=False,
        diagnose=False,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "{name}:{function}:{line} | "
            "<level>{message}</level>"
        ),
    )

    intercept_handler = InterceptHandler()
    logging.basicConfig(handlers=[intercept_handler], level=0, force=True)

    for logger_name in _intercepted_loggers():
        target_logger = logging.getLogger(logger_name)
        target_logger.handlers = [intercept_handler]
        target_logger.propagate = False


def _intercepted_loggers() -> Iterable[str]:
    return (
        "uvicorn",
        "uvicorn.access",
        "uvicorn.error",
        "fastapi",
        "sqlalchemy",
        "sqlalchemy.engine",
        "alembic",
        "celery",
    )
