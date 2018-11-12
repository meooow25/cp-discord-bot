import logging
import platform
from datetime import timedelta, timezone
from operator import itemgetter

from . import command, commands
from .discord import Channel
from .models import User


class Bot:
    PYTHON_URL = 'https://www.python.org'
    GITHUB_URL = 'https://github.com/meooow25/cp-discord-bot'
    CONTESTS_PER_PAGE = 5
    # TODO: Support separate time zones per channel or server
    TIMEZONE = timezone(timedelta(hours=5, minutes=30))

    def __init__(self, name, client, site_container, entity_manager, triggers=None, allowed_channels=None):
        self.name = name
        self.client = client
        self.site_container = site_container
        self.entity_manager = entity_manager
        self.triggers = triggers
        self.allowed_channels = allowed_channels
        self.logger = logging.getLogger(self.__class__.__qualname__)

        self.command_map = {}
        for attr_name in dir(commands):
            attr = getattr(commands, attr_name)
            if isinstance(attr, command.Command):
                cmd = attr
                self.command_map[cmd.name] = cmd
        self.logger.info(f'Loaded commands: {self.command_map.keys()}')

        # Help message begin.
        self.help_message = {}
        if not triggers:
            self.help_message['content'] = '*@mention me to activate me.*\n'
        else:
            self.help_message['content'] = f'*@mention me or use my trigger `{self.triggers[0]}` to activate me.*\n'

        fields = [cmd.embed_field_rep() for cmd in self.command_map.values() if not cmd.hidden]
        fields.sort(key=itemgetter('name'))
        self.help_message['embed'] = {
            'title': 'Supported commands:',
            'fields': fields,
        }

        # Info message begin.
        self.info_message = {
            'content': f'*Hello, I am **{self.name}**!*',
            'embed': {
                'description': f'A half-baked bot made by *meooow*\n'
                               f'Written in awesome [Python 3.7]({self.PYTHON_URL})\n'
                               f'Check me out on [Github]({self.GITHUB_URL})!',
            },
        }

        # Status message begin.
        self.status_message = {
            'content': '*Status info*',
            'embed': {
                'fields': [
                    {
                        'name': 'System',
                        'value': f'Python version: {platform.python_version()}\n'
                                 f'OS and version: {platform.system()}-{platform.release()}',
                    },
                ],
            },
        }

    async def run(self):
        """Runs the entity manager, site container, and Discord client."""
        await self.entity_manager.run()
        await self.site_container.run(get_all_users=self.get_all_users,
                                      on_profile_fetch=self.on_profile_fetch)
        await self.client.run(on_message=self.on_message)

    async def on_message(self, message):
        """Callback intended to be executed when the Discord client receives a message."""

        # message.author is None when message is sent by a webhook.
        if not message.author or message.author.bot:
            return

        args = message.content.split()
        if not args:
            return
        has_trigger = args[0] in self.triggers if self.triggers else False
        has_trigger = has_trigger or args[0] == f'<@{self.client.user["id"]}>'
        if has_trigger:
            args = args[1:]
            if not args:
                return
        on_allowed_channel = self.allowed_channels is None or message.channel_id in self.allowed_channels

        channel = await self.get_channel(message.channel_id)
        if channel.type == Channel.Type.DM:
            await self.run_command_from_map(args, message, is_dm=True)
        elif has_trigger and on_allowed_channel:
            await self.run_command_from_map(args, message, is_dm=False)

    async def run_command_from_map(self, args, message, is_dm):
        """Executes the command named ``args[0]`` if it exists."""

        # Ignore command case.
        args[0] = args[0].lower()
        cmd = self.command_map.get(args[0])
        if cmd is None:
            self.logger.info(f'Unrecognized command {args}')
            return
        if cmd.allow_dm and is_dm or cmd.allow_guild and not is_dm:
            try:
                await cmd.execute(self, args[1:], message)
            except command.IncorrectUsageException as ex:
                self.logger.info(f'Incorrect usage: {ex}')
        else:
            self.logger.info(f'Command not allowed in current channel type (guild/DM): "{message.content}"')

    async def get_channel(self, channel_id):
        """Returns the Discord channel with given channel id.

        Attempts to find the channel is the entity manager first. If not found, the client is queried and the returned
        channel saved to the entity manager before returning.
        """
        channel = self.entity_manager.get_channel(channel_id)
        if channel is None:
            channel = await self.client.get_channel(channel_id)
            await self.entity_manager.save_channel(channel)
        return channel

    def get_all_users(self):
        """Returns a shallow copy of the list of all users."""
        return self.entity_manager.users[:]

    async def on_profile_fetch(self, user, old_profile, new_profile):
        """Callback intended to be executed when the site container updates a user site profile."""

        changed = await self.entity_manager.update_user_site_profile(user.discord_id, new_profile)
        if not changed:
            return
        self.logger.debug(f'Changed profile: {old_profile.to_dict()}, {new_profile.to_dict()}')
        msg = {
            'content': '*Your profile has been updated*',
            'embed': User.get_profile_change_embed(old_profile, new_profile)
        }
        await self.client.send_message(msg, user.dm_channel_id)
