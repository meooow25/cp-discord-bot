import logging

from bot.models import User
from discord.models import Channel


class Manager:

    def __init__(self, db_connector):
        self.db_connector = db_connector
        self.users = None
        self.user_id_to_user = None
        self.channel_id_to_channel = None
        self.logger = logging.getLogger(self.__class__.__qualname__)

    async def run(self):
        self.db_connector.connect()
        await self.load_users()
        await self.load_channels()

    async def load_users(self):
        users = await self.db_connector.get_all_users()
        self.users = [User.from_dict(user) for user in users]
        self.user_id_to_user = {user.discord_id: user for user in self.users}
        self.logger.info(f'Loaded {len(self.users)} users from db')

    async def load_channels(self):
        channels = await self.db_connector.get_all_channels()
        channels = [Channel.from_dict(channel) for channel in channels]
        self.channel_id_to_channel = {channel.id: channel for channel in channels}
        self.logger.info(f'Loaded {len(channels)} channels from db')

    async def set_user_site_profile(self, user_id, profile):
        user = self.user_id_to_user.get(user_id)
        if user is None:
            user = User(user_id)
            self.user_id_to_user[user_id] = user
        user.site_profiles = [curr_profile for curr_profile in user.site_profiles if curr_profile.site != profile.site]
        user.site_profiles.append(profile)
        # TODO: Optimize to update instead of replace.
        await self.db_connector.put_user(user.to_dict())
        self.logger.info(f'Saved user with id {user_id} to db')

    def get_channel(self, channel_id):
        return self.channel_id_to_channel.get(channel_id)

    async def save_channel(self, channel):
        self.channel_id_to_channel[channel.id] = channel
        await self.db_connector.put_channel(channel.to_dict())
        self.logger.info(f'Saved channel with id {channel.id} to db')
