import logging
import os
from typing import Optional

import dotenv

from .utils import getenv, getenv_typed


class Config:
    production: bool
    environment: str
    log_directory: str
    log_file: str
    log_level: str
    telegram_bot_token: str
    developer_chat_id: int
    notify_chat_ids: list[int]

    @staticmethod
    def __load_dotenv():
        dotenv_path = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
        print(dotenv_path)
        dotenv.load_dotenv(dotenv_path=dotenv_path, override=False)

    @staticmethod
    def load():
        Config.__load_dotenv()

        Config.production = getenv('PY_ENVIRONMENT', 'development') == 'production'
        Config.environment = getenv('PY_ENVIRONMENT', 'development')
        Config.log_directory = getenv('LOG_DIR')
        Config.log_file = getenv('LOG_FILE')
        Config.log_level = getenv('LOG_LEVEL', 'DEBUG')
        Config.telegram_bot_token = getenv('TELEGRAM_BOT_TOKEN')
        Config.developer_chat_id = getenv_typed('DEVELOPER_CHAT_ID', int)
        Config.notify_chat_ids = list(map(int, getenv('NOTIFY_CHAT_IDS').split(',')))

        if not os.path.exists(Config.log_directory):
            os.mkdir(Config.log_directory)

    @staticmethod
    def setup_app_logger(log_file: Optional[str] = None):
        logger = logging.getLogger('app')
        logger.setLevel(Config.log_level)
        formatter = logging.Formatter(
            '[%(asctime)s] #%(thread)d [%(levelname)s] %(name)s: %(message)s', datefmt='%d/%b/%Y:%H:%M:%S')

        # create a StreamHandler to log to the console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(Config.log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # create a FileHandler to log to a file
        file_handler = logging.FileHandler(os.path.join(Config.log_directory, log_file or Config.log_file))
        file_handler.setLevel(Config.log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
