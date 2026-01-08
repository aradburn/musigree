import logging.config
from typing import Any

LOGGING_TRACE: bool = False

LOGGING_CONFIG: dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S%z",
        },
        "error": {
            "format": "%(asctime)s-%(levelname)s-%(name)s-%(process)d::%(module)s|%(lineno)s:: %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S%z",
        },
    },
    "handlers": {
        "default": {
            "level": "INFO",
            "formatter": "standard",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",  # Default is stderr
        },
        "console_handler": {
            "level": "INFO",
            "formatter": "standard",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        # "rotating_file_handler": {
        #     "level": "INFO",
        #     "formatter": "standard",
        #     "class": "logging.handlers.RotatingFileHandler",
        #     "filename": LOGGING_FILE,
        #     "mode": "a",
        #     "maxBytes": 1048576,
        #     "backupCount": 10,
        # },
        # "error_file_handler": {
        #     "level": "WARNING",
        #     "formatter": "error",
        #     "class": "logging.FileHandler",
        #     "filename": LOGGING_ERROR_FILE,
        #     "mode": "a",
        # },
        # "critical_mail_handler": {
        #     "level": "CRITICAL",
        #     "formatter": "error",
        #     "class": "logging.handlers.SMTPHandler",
        #     "mailhost": "localhost",
        #     "fromaddr": "monitoring@musigree.com",
        #     "toaddrs": ["dev@musigree.com", "qa@musigree.com"],
        #     "subject": "Critical error with Musigree application",
        # },
    },
    "loggers": {
        "": {  # root logger
            "handlers": ["default"],
            "level": "WARNING",
            "propagate": False,
        },
        "musigree": {
            "handlers": ["console_handler"],
            "level": "DEBUG",
            "propagate": False,
        },
        "tests": {
            "handlers": ["console_handler"],
            "level": "ERROR",
            "propagate": False,
        },
        "uvicorn": {
            "handlers": ["console_handler"],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.error": {
            "handlers": ["console_handler"],
            "level": "DEBUG",
            "propagate": False,
        },
        "uvicorn.access": {
            "handlers": ["console_handler"],
            "level": "DEBUG",
            "propagate": False,
        },
        "fastapi": {
            "handlers": ["console_handler"],
            "level": "DEBUG",
            "propagate": False,
        },
        "__main__": {  # if __name__ == '__main__'
            "handlers": ["console_handler"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

TEST_LOGGING_CONFIG: dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S%z",
        },
        "error": {
            "format": "%(asctime)s-%(levelname)s-%(name)s-%(process)d::%(module)s|%(lineno)s:: %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S%z",
        },
    },
    "handlers": {
        "default": {
            "level": "DEBUG",
            "formatter": "standard",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",  # Default is stderr
        },
        "console_handler": {
            "level": "DEBUG",
            "formatter": "standard",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        # "debug_file_handler": {
        #     "level": "DEBUG",
        #     "formatter": "standard",
        #     "class": "logging.FileHandler",
        #     "filename": LOGGING_DEBUG_FILE,
        #     # "mode": "a",
        # },
    },
    "loggers": {
        "": {  # root logger
            "handlers": ["default"],
            "level": "DEBUG",
            "propagate": False,
        },
        "musigree": {
            "handlers": ["console_handler"],
            "level": "DEBUG",
            "propagate": False,
        },
        "tests": {
            "handlers": ["console_handler"],
            "level": "DEBUG",
            "propagate": False,
        },
        "uvicorn": {
            "handlers": ["console_handler"],
            "level": "WARN",
            "propagate": False,
        },
        "uvicorn.error": {
            "handlers": ["console_handler"],
            "level": "WARN",
            "propagate": False,
        },
        "uvicorn.access": {
            "handlers": ["console_handler"],
            "level": "DEBUG",
            "propagate": False,
        },
        "fastapi": {
            "handlers": ["console_handler"],
            "level": "DEBUG",
            "propagate": False,
        },
        "starlette": {
            "handlers": ["console_handler"],
            "level": "DEBUG",
            "propagate": False,
        },
        "httpx": {
            "handlers": ["console_handler"],
            "level": "DEBUG",
            "propagate": False,
        },
        "httpcore": {
            "handlers": ["console_handler"],
            "level": "DEBUG",
            "propagate": False,
        },
        "sqlalchemy.engine": {
            "handlers": ["console_handler"],
            "level": "WARN",
            "propagate": False,
        },
        "sqlalchemy.dialects.postgresql": {
            "handlers": ["console_handler"],
            "level": "WARN",
            "propagate": False,
        },
        "sqlalchemy.pool": {
            "handlers": ["console_handler"],
            "level": "WARN",
            "propagate": False,
        },
        "asyncio": {
            "handlers": ["console_handler"],
            "level": "WARN",
            "propagate": False,
        },
        "aiosqlite": {
            "handlers": ["console_handler"],
            "level": "WARN",
            "propagate": False,
        },
        "__main__": {  # if __name__ == '__main__'
            "handlers": ["console_handler"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}


def setup_logging(is_testing: bool = False) -> None:
    # Run once at startup:
    config = LOGGING_CONFIG if is_testing is False else TEST_LOGGING_CONFIG
    logging.config.dictConfig(config)

    # Include this next line in each module that needs logging:
    log = logging.getLogger(__name__)
    log.info("")
    log.info("Logging configured OK.")


def shutdown_logging() -> None:
    loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
    if len(loggers) > 0:
        log = logging.getLogger(__name__)
        log.info("Shutting down logging.")
        logging.shutdown()
