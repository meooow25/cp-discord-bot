
import asyncio
import logging
import os

from bot.bot import Bot

TOKEN = os.environ['TOKEN']
NAME = 'CPBot'
TRIGGERS = ['.cp']
CHANNELS = ['channel_id']
AUTHOR = 'author_id'


def main():
    logging.basicConfig(level=logging.WARNING)
    bot = Bot(TOKEN, name=NAME, author_id=AUTHOR, triggers=TRIGGERS, allowed_channels=CHANNELS)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(bot.run())
    loop.close()


if __name__ == '__main__':
    main()
