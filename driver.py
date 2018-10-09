import argparse
import asyncio
import logging
import os

from bot.bot import Bot
from bot.entity_manager import EntityManager
from db.mongodb_connector import MongoDBConnector
from discord.client import Client
from sites.atcoder import AtCoder
from sites.codechef import CodeChef
from sites.codeforces import Codeforces
from sites.site_container import SiteContainer

logger = logging.getLogger(__name__)

DISCORD_TOKEN = os.environ['DISCORD_TOKEN']
MONGODB_SRV = os.environ['MONGODB_SRV']

NAME = 'Bot'
TRIGGERS = ['trigger']
CHANNELS = ['channel_id']
ACTIVITY_NAME = 'activity'
DB_NAME = 'db'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--log', default='WARNING')
    args = parser.parse_args()
    numeric_level = getattr(logging, args.log.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {args.log}')
    logging.basicConfig(format='{levelname}:{name}:{message}', style='{', level=numeric_level)

    discord_client = Client(DISCORD_TOKEN, name=NAME, activity_name=ACTIVITY_NAME)
    mongodb_connector = MongoDBConnector(MONGODB_SRV, DB_NAME)
    entity_manager = EntityManager(mongodb_connector)
    sites = [AtCoder(), CodeChef(), Codeforces()]
    site_container = SiteContainer(sites=sites)

    bot = Bot(NAME, discord_client, site_container, entity_manager, triggers=TRIGGERS, allowed_channels=CHANNELS)

    try:
        asyncio.run(bot.run())
    except Exception as ex:
        logger.exception('Grinding halt')


if __name__ == '__main__':
    main()
