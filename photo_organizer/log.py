import logging
import platform
from logging.config import dictConfig
from pathlib import Path
from typing import Optional

FORMAT = "%(asctime)s {app} [%(thread)d] %(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]"
DATE_FORMAT = None


def setup_logging(
    name: str, level: str = "INFO", fmt: str = FORMAT, log_dir: Optional[str] = None
) -> None:
    formatted = fmt.format(app=name)

    if log_dir is None:
        if platform.system() == "Windows":
            log_dir = Path(r"C:/Users/sherd/Documents/GitHub/photo_organizer")
        else:
            log_dir = Path.cwd() / "log"
    else:
        log_dir = Path(log_dir)

    log_dir.mkdir(parents=True, exist_ok=True)

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"standard": {"format": formatted}},
        "handlers": {
            "default": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "level": "DEBUG",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.TimedRotatingFileHandler",
                "when": "midnight",
                "utc": True,
                "backupCount": 5,
                "level": level,
                "filename": str(log_dir / "photo_organizer.log"),
                "formatter": "standard",
            },
        },
        "loggers": {"": {"handlers": ["default", "file"], "level": level}},
    }

    dictConfig(logging_config)
