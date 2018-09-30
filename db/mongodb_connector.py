import asyncio
import logging
import motor.motor_asyncio


class MongoDBConnector:
    def __init__(self, srv):
        self.srv = srv
        self.client = None
        self.db = None
        self.logger = logging.getLogger(self.__class__.__qualname__)

    def connect(self):
        self.logger.debug('Connecting to MongoDB')
        loop = asyncio.get_running_loop()
        self.client = motor.motor_asyncio.AsyncIOMotorClient(self.srv, io_loop=loop)
        self.db = self.client.discord_db

    async def put_user(self, user):
        await self.db.users.replace_one({'discord_id': user['discord_id']}, user, upsert=True)

    async def put_channel(self, channel):
        await self.db.channels.replace_one({'id': channel['id']}, channel, upsert=True)

    async def get_all_users(self):
        cursor = self.db.users.find()
        return await cursor.to_list(length=None)

    async def get_all_channels(self):
        cursor = self.db.channels.find()
        return await cursor.to_list(length=None)
