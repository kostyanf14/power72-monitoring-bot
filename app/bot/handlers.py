import html
import json
import logging
import traceback

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from app.config import Config
from app.status import Status

logger = logging.getLogger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    logger.error(msg="Exception while handling an update:",
                 exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_msg = context.error.__traceback__ if context.error is not None else None
    tb_list = traceback.format_exception(None, context.error, tb_msg)
    tb_string = "".join(tb_list)

    # Build the message with some markup and additional information about what happened.
    # You might need to add some logic to deal with messages longer than the 4096 character limit.
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        f"An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )

    # Finally, send the message
    # max message size 4096
    await context.bot.send_message(
        chat_id=Config.developer_chat_id, text=message[:4000], parse_mode=ParseMode.HTML
    )


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.debug("bot_start_cmd %s", update)

    if update.message is None:
        logger.error("bot_start_cmd with message/text None")
        return

    await update.message.reply_text('bot_start_cmd: /status')


async def help_cmd(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.debug("bot_help_cmd %s", update)

    if update.message is None:
        logger.error("bot_help_cmd with message None")
        return

    await update.message.reply_text('bot_help_cmd')


async def status_cmd(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.debug("bot_status_cmd %s", update)

    if update.message is None:
        logger.error("bot_status_cmd with message None")
        return

    await update.message.reply_text(Status().generate_status_msg(), parse_mode=ParseMode.MARKDOWN_V2)
