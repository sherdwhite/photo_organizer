import logging
import platform
from logging.config import dictConfig
from pathlib import Path
from typing import Optional

# Default log format with detailed information for file logging
FORMAT = (
    "%(asctime)s {app} [%(thread)d] %(levelname)-5s %(name)s - "
    "%(message)s. [file=%(filename)s:%(lineno)d]"
)

# Console format (simpler for readability)
CONSOLE_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Default log format with detailed information for file logging
FORMAT = (
    "%(asctime)s {app} [%(thread)d] %(levelname)-5s %(name)s - "
    "%(message)s. [file=%(filename)s:%(lineno)d]"
)

# Console format (simpler for readability)
CONSOLE_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    name: str,
    level: str = "INFO",
    fmt: str = FORMAT,
    log_dir: Optional[str] = None,
    console_level: str = "INFO",
    enable_file_logging: bool = True,
) -> None:
    """
    Set up logging configuration for the Photo Organizer application.

    This function configures both console and file logging with appropriate
    formatters and handlers. The log file location can be dynamically set
    based on the photo processing destination directory.

    Args:
        name: Application name to include in log messages
        level: Minimum log level for file logging ("DEBUG", "INFO", "WARNING",
               "ERROR", "CRITICAL")
        fmt: Log message format string (defaults to detailed format)
        log_dir: Directory where log files should be stored. If None, uses:
                - On Windows: Current working directory
                - On Unix/Linux: ./log subdirectory
                If processing photos, this should be set to the destination
                directory for better organization
        console_level: Minimum log level for console output (defaults to "INFO")
        enable_file_logging: Whether to enable file logging (defaults to True)

    Returns:
        None

    Examples:
        # Basic setup (logs to current directory)
        setup_logging("photo_organizer")

        # Setup with custom destination (recommended for photo processing)
        setup_logging("photo_organizer", log_dir="/path/to/sorted/photos")

        # Debug mode with verbose console output
        setup_logging("photo_organizer", level="DEBUG", console_level="DEBUG")

        # Console-only logging (no file output)
        setup_logging("photo_organizer", enable_file_logging=False)

    Note:
        - Log files are rotated daily at midnight (UTC) with 5 days retention
        - File logs include detailed context (thread, file, line number)
        - Console logs use a simpler, more readable format
        - This function should be called early in application startup
    """
    # Format the log message template with app name
    formatted = fmt.format(app=name)
    console_formatted = CONSOLE_FORMAT.format(app=name)

    # Determine log directory
    if log_dir is None:
        if platform.system() == "Windows":
            # Use current working directory on Windows
            log_dir = Path.cwd()
        else:
            # Use log subdirectory on Unix/Linux systems
            log_dir = Path.cwd() / "log"
    else:
        log_dir = Path(log_dir)

    # Ensure log directory exists
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create log file path
    log_file_path = log_dir / "photo_organizer.log"

    # Build logging configuration
    handlers_config = {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "console",
            "level": console_level,
            "stream": "ext://sys.stdout",
        }
    }

    formatters_config = {
        "console": {"format": console_formatted, "datefmt": DATE_FORMAT}
    }

    # Add file handler if enabled
    if enable_file_logging:
        handlers_config["file"] = {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "when": "midnight",
            "utc": True,
            "backupCount": 5,
            "level": level,
            "filename": str(log_file_path),
            "formatter": "detailed",
            "encoding": "utf-8",  # Ensure proper encoding for file logs
        }
        formatters_config["detailed"] = {"format": formatted, "datefmt": DATE_FORMAT}

    # Configure root logger handlers
    root_handlers = ["console"]
    if enable_file_logging:
        root_handlers.append("file")

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": formatters_config,
        "handlers": handlers_config,
        "loggers": {
            "": {  # Root logger
                "handlers": root_handlers,
                "level": "DEBUG",  # Let handlers filter the level
                "propagate": False,
            }
        },
    }

    # Apply the configuration
    dictConfig(logging_config)

    # Log the configuration for debugging
    logger = logging.getLogger(__name__)
    logger.info("Logging initialized for %s", name)
    if enable_file_logging:
        logger.info("Log file location: %s", log_file_path)
    logger.debug(
        "Console log level: %s, File log level: %s",
        console_level,
        level if enable_file_logging else "DISABLED",
    )
