import argparse
import asyncio
import logging
import os

from bot.bot import Bot

logger = logging.getLogger(__name__)

TOKEN = os.environ['TOKEN']
NAME = 'Bot'
TRIGGERS = ['trigger']
CHANNELS = ['channel_id']
AUTHOR = 'author_id'
ACTIVITY_NAME = 'activity'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--log', default='WARNING')
    args = parser.parse_args()
    numeric_level = getattr(logging, args.log.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {args.log}')
    logging.basicConfig(level=numeric_level)
    bot = Bot(TOKEN, name=NAME, activity_name=ACTIVITY_NAME, author_id=AUTHOR, triggers=TRIGGERS,
              allowed_channels=CHANNELS)
    try:
        asyncio.run(bot.run())
    except Exception as ex:
        logger.critical(f'Exception: {ex}')


if __name__ == '__main__':
    main()
