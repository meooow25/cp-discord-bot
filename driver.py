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
    loop = asyncio.get_event_loop()
    main_task = asyncio.ensure_future(bot.run())

    async def stop():
        loop.stop()

    def cancel_pending_tasks(future):
        """Main task should never end, error expected"""
        logger.error(f'Main task completed with error: {future.exception()}')
        for task in asyncio.Task.all_tasks():
            logger.error(f'Cancelling task {task}')
            task.cancel()
        asyncio.ensure_future(stop())

    main_task.add_done_callback(cancel_pending_tasks)
    try:
        loop.run_forever()
    finally:
        loop.close()


if __name__ == '__main__':
    main()
