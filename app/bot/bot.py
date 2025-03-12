import asyncio
import logging
from typing import Optional

from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler

from app.config import Config
from app.status.status import Status
from app.utils import SingletonMeta

from . import handlers

logger = logging.getLogger(__name__)


class Bot(metaclass=SingletonMeta):
    loop: Optional[asyncio.AbstractEventLoop]

    def __init__(self) -> None:
        logger.info("Initializing bot")
        telegram_bot_token = Config.telegram_bot_token
        self.application = Application.builder().token(telegram_bot_token).build()
        self.loop = None
        self.__register_handlers__()

    def __register_handlers__(self) -> None:
        logger.info("Registering handlers")
        self.application.add_handler(CommandHandler(
            'start', handlers.start_cmd, block=False))
        self.application.add_handler(CommandHandler(
            'status', handlers.status_cmd, block=False))
        self.application.add_handler(CommandHandler(
            'help', handlers.help_cmd, block=False))

        logger.debug("Registering error handlers")
        self.application.add_error_handler(handlers.error_handler)

    async def send_status_update(self, triggered_by: list[str]) -> None:
        logger.info("Sending status update")

        msg = Status().generate_status_msg(triggered_by)
        for chat_id in Config.notify_chat_ids:
            await self.application.bot.sendMessage(chat_id=chat_id, text=msg, parse_mode=ParseMode.MARKDOWN_V2)

        logger.debug("Status update sent")

    def start(self) -> None:
        logger.info('Starting bot polling')
        self.loop = asyncio.get_event_loop()
        print(f"bot_start -> {self.loop}")
        self.application.run_polling()
        logger.debug('Run polling exited')

    def stop(self) -> None:
        logger.info('Stopping bot')
        if self.loop is None:
            logger.warning('Bot appears to not be running (loop is None)')
        else:
            self.loop.stop()
        logger.debug('Stopped current event loop')
