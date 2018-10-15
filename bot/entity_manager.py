import logging

from .models import User
from .discord import Channel


class EntityManager:
    """Responsible for managing users and channels.

     Loads entities from the database on start up, and saves them to the database on modification.
    """

    def __init__(self, db_connector):
        self.db_connector = db_connector
        self.users = None
        self._user_id_to_user = None
        self._channel_id_to_channel = None
        self.logger = logging.getLogger(self.__class__.__qualname__)

    async def run(self):
        """Connects to the database and loads users and channels."""
        self.logger.debug('Running EntityManager...')
        self.db_connector.connect()
        await self._load_users()
        await self._load_channels()

    async def _load_users(self):
        users = await self.db_connector.get_all_users()
        self.users = [User.from_dict(user) for user in users]
        self._user_id_to_user = {user.discord_id: user for user in self.users}
        self.logger.info(f'Loaded {len(self.users)} users from db')

    async def _load_channels(self):
        channels = await self.db_connector.get_all_channels()
        channels = [Channel(**channel_d) for channel_d in channels]
        self._channel_id_to_channel = {channel.id: channel for channel in channels}
        self.logger.info(f'Loaded {len(channels)} channels from db')

    def get_user(self, user_id):
        """Looks up and returns a user by the user's Discord id, ``None`` if there is no such user"""
        return self._user_id_to_user.get(user_id)

    def create_user(self, user_id, dm_channel_id):
        """Creates a new user with given Discord id and DM channel id. Does nothing if user already exists."""
        user = self._user_id_to_user.get(user_id)
        if user is None:
            user = User(user_id, dm_channel_id)
            self.users.append(user)
            self._user_id_to_user[user_id] = user

    async def update_user_site_profile(self, user_id, profile):
        """Creates or updates a user's site profile to the given profile."""
        user = self._user_id_to_user.get(user_id)
        changed = user.update_profile(profile)
        # TODO: Optimize to update instead of replace.
        if changed:
            await self.db_connector.put_user(user.to_dict())
            self.logger.info(f'Saved user with id {user_id} to db')
        return changed

    async def delete_user_site_profile(self, user_id, site_tag):
        """Deletes a user's site profile associated with the given site tag."""
        user = self._user_id_to_user.get(user_id)
        changed = user.delete_profile(site_tag)
        # TODO: Optimize to update instead of replace.
        if changed:
            await self.db_connector.put_user(user.to_dict())
            self.logger.info(f'Saved user with id {user_id} to db')
        return changed

    def get_channel(self, channel_id):
        """Returns the channel with the given id, or ``None`` if no channel with given id is found."""
        return self._channel_id_to_channel.get(channel_id)

    async def save_channel(self, channel):
        """Saves the given channel."""
        self._channel_id_to_channel[channel.id] = channel
        await self.db_connector.put_channel(channel.to_dict())
        self.logger.info(f'Saved channel with id {channel.id} to db')
