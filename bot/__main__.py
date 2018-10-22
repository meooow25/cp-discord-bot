import argparse
import asyncio
import json
import logging
import os

from .bot import Bot
from .entity_manager import EntityManager
from .db import MongoDBConnector
from .discord import Client
from .sites import AtCoder, CodeChef, Codeforces, SiteContainer

logger = logging.getLogger(__name__)

DISCORD_TOKEN = os.environ['DISCORD_TOKEN']
MONGODB_SRV = os.environ['MONGODB_SRV']

with open('./bot/config.json') as file:
    CONFIG = json.load(file)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--log', default='WARNING')
    args = parser.parse_args()
    numeric_level = getattr(logging, args.log.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {args.log}')
    logging.basicConfig(format='{levelname}:{name}:{message}', style='{', level=numeric_level)

    discord_client = Client(DISCORD_TOKEN, name=CONFIG['name'], activity_name=CONFIG['activity'])
    mongodb_connector = MongoDBConnector(MONGODB_SRV, CONFIG['db_name'])
    entity_manager = EntityManager(mongodb_connector)
    sites = [
        AtCoder(**CONFIG['at_config']),
        CodeChef(**CONFIG['cc_config']),
        Codeforces(**CONFIG['cf_config']),
    ]
    site_container = SiteContainer(sites=sites)

    bot = Bot(CONFIG['name'], discord_client, site_container, entity_manager,
              triggers=CONFIG['triggers'], allowed_channels=CONFIG['channels'])

    try:
        asyncio.run(bot.run())
    except Exception:
        logger.exception('Grinding halt')


if __name__ == '__main__':
    main()
