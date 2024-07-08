import asyncio
import os
import time

import requests

from app.bot import Bot
from app.config import Config
from app.status import Status


async def print_status():
    print(Status().generate_status_msg())


def main_bot():
    Config.load()
    Config.setup_app_logger('app_bot.log')

    app_dir = os.path.dirname(os.path.realpath(__file__))
    Status().init(os.path.join(app_dir, "config.json"))

    if Config.environment == 'local':
        Status().start_monitoring(print_status)
        asyncio.get_event_loop().run_forever()
    else:
        Status().start_monitoring(Bot().send_status_update)
        Bot().start()


def exit_bot():
    if Config.environment != 'local':
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
