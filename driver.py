import argparse
import asyncio
import logging
import os

from bot.bot import Bot

TOKEN = os.environ['TOKEN']
NAME = 'Bot'
TRIGGERS = ['.cp']
CHANNELS = ['channel_id']
AUTHOR = 'author_id'
ACTIVITY_NAME = 'activity'


def main(loglevel):
    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % loglevel)
    logging.basicConfig(level=numeric_level)
    bot = Bot(TOKEN, name=NAME, activity_name=ACTIVITY_NAME, author_id=AUTHOR, triggers=TRIGGERS,
              allowed_channels=CHANNELS)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(bot.run())
    loop.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--log', default='WARNING')
    args = parser.parse_args()
    loglevel = vars(args).get('log')
    main(loglevel)
