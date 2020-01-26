import os
import platform

from logging.config import dictConfig

FORMAT = "%(asctime)s {app} [%(thread)d] %(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]"
DATE_FORMAT = None


def setup_logging(name, level="INFO", fmt=FORMAT):
    formatted = fmt.format(app=name)
    if platform.system() == 'Windows':
        log_dir = r'D:/log'
    else:
        log_dir = "{}/log".format(os.getcwd())
        
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logging_config = {
        "version": 1,
        'disable_existing_loggers': False,
        "formatters": {
            'standard': {
                'format': formatted
            }
        },
        "handlers": {
            'default': {
                'class': 'logging.StreamHandler',
                'formatter': 'standard',
                'level': level,
                'stream': 'ext://sys.stdout'
            },
            'file': {
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'when': 'midnight',
                'utc': True,
                'backupCount': 5,
                'level': level,
                'filename': '{}/app_manager.log'.format(log_dir),
                'formatter': 'standard',
            }
        },
        "loggers": {
            "": {
                'handlers': ['default', 'file'],
                'level': level
            }
        }
    }

    dictConfig(logging_config)
