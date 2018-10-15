import asyncio
import logging
import motor.motor_asyncio


class MongoDBConnector:
    """Handles connection with a MongoDB database."""

    def __init__(self, srv_url, db_name):
        self.srv_url = srv_url
        self.db_name = db_name
        self.client = None
        self.db = None
        self.logger = logging.getLogger(self.__class__.__qualname__)

    def connect(self):
        """Initialize MongoDB client to provided database."""
        self.logger.info('Connecting to MongoDB')
        loop = asyncio.get_running_loop()
        self.client = motor.motor_asyncio.AsyncIOMotorClient(self.srv_url, io_loop=loop)
        self.db = self.client[self.db_name]

    async def put_user(self, user):
        """Store a user to the database."""
        await self.db.users.replace_one({'discord_id': user['discord_id']}, user, upsert=True)

    async def put_channel(self, channel):
        """Store a channel to the database."""
        await self.db.channels.replace_one({'id': channel['id']}, channel, upsert=True)

    async def get_all_users(self):
        """Retrieve a list of all users from the database."""
        cursor = self.db.users.find()
        return await cursor.to_list(length=None)

    async def get_all_channels(self):
        """Retrieve a list of all channels from the database."""
        cursor = self.db.channels.find()
        return await cursor.to_list(length=None)
