from app.bot import Bot
from app.config import Config
from app.status import Status


def main_bot():
    Config.load()
    Config.setup_app_logger('app_bot.log')
    Status().init()
    Status().start_monitoring(Bot().send_status_update)
    Bot().start()


def exit_bot():
    Bot().stop()


if __name__ == '__main__':
    main_bot()
    exit_bot()
