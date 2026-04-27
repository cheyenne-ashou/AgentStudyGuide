"""
Structured logging via structlog.

Usage:
    from core.logger import get_logger
    log = get_logger(__name__)
    log.info("agent.step", step=1, tool="calculator", result="47")
"""
import logging
import sys
import structlog

_configured = False


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper()),
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="%H:%M:%S"),
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )


def get_logger(name: str) -> structlog.BoundLogger:
    global _configured
    if not _configured:
        setup_logging()
        _configured = True
    return structlog.get_logger(name)
