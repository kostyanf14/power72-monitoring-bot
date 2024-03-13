import time
import requests
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
    for i in range(5):
        try:
            response = requests.get("https://1.1.1.1", timeout=60)
            print("The Internet is connected.")
            break
        except requests.ConnectionError:
            print("The Internet is not connected. Waiting 60 seconds to try again.")
            time.sleep(60)

    main_bot()
    exit_bot()
