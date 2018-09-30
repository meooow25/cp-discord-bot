import argparse
import asyncio
import logging
import os

from bot.bot import Bot
from bot.manager import Manager
from db.mongodb_connector import MongoDBConnector
from discord.client import Client
from sites.atcoder import AtCoder
from sites.codechef import CodeChef
from sites.codeforces import Codeforces
from sites.composite_site import CompositeSite

logger = logging.getLogger(__name__)

DISCORD_TOKEN = os.environ['DISCORD_TOKEN']
MONGODB_SRV = os.environ['MONGODB_SRV']

NAME = 'Bot'
TRIGGERS = ['trigger']
CHANNELS = ['channel_id']
ACTIVITY_NAME = 'activity'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--log', default='WARNING')
    args = parser.parse_args()
    numeric_level = getattr(logging, args.log.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {args.log}')
    logging.basicConfig(format='{levelname}:{name}:{message}', style='{', level=numeric_level)

    client = Client(DISCORD_TOKEN, name=NAME, activity_name=ACTIVITY_NAME)
    sites = [AtCoder(), CodeChef(), Codeforces()]
    site = CompositeSite(sites=sites)
    mongodb_connector = MongoDBConnector(MONGODB_SRV)
    manager = Manager(mongodb_connector)
    bot = Bot(NAME, client, site, manager, triggers=TRIGGERS, allowed_channels=CHANNELS)

    try:
        asyncio.run(bot.run())
    except Exception as ex:
        logger.exception('Grinding halt')


if __name__ == '__main__':
    main()
