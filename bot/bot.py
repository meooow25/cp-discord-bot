import json
import logging
import platform
from datetime import timedelta, timezone
from operator import itemgetter

from discord.models import Channel
from . import guild_channel_commands, dm_channel_commands
from .command import Command

logger = logging.getLogger(__name__)


class Bot:
    AUTHOR_ID = 'author_id'
    GITHUB_URL = 'https://github.com/meooow25/cp-discord-bot'
    MSG_MAX_CONTESTS = 5
    # TODO: Support separate time zones per channel or server
    TIME_ZONE = timezone(timedelta(hours=5, minutes=30))

    def __init__(self, name, client, site, manager, triggers=None, allowed_channels=None):
        self.name = name
        self.client = client
        self.site = site
        self.manager = manager
        self.triggers = triggers
        self.allowed_channels = allowed_channels

        self.client.on_message = self.on_message

        self.guild_channel_command_map = {}
        for attr_name in dir(guild_channel_commands):
            attr = getattr(guild_channel_commands, attr_name)
            if isinstance(attr, Command):
                command = attr
                self.guild_channel_command_map[command.name] = command
        logger.info(f'Loaded guild channel commands: {self.guild_channel_command_map.keys()}')

        self.dm_channel_command_map = {}
        for attr_name in dir(dm_channel_commands):
            attr = getattr(dm_channel_commands, attr_name)
            if isinstance(attr, Command):
                command = attr
                self.dm_channel_command_map[command.name] = command
        logger.info(f'Loaded DM channel commands: {self.dm_channel_command_map.keys()}')

        # Help message begin.
        self.help_message = {}
        if not triggers:
            self.help_message['content'] = '*@mention me to activate me.*\n'
        else:
            self.help_message['content'] = f'*@mention me or use my trigger `{self.triggers[0]}` to activate me.*\n'
        # TODO: Add DM channel commands to help message.
        self.help_message['embed'] = {
            'title': 'Supported commands:',
            'fields': [{
                'name': f'`{command.usage}`',
                'value': command.desc,
            } for command in self.guild_channel_command_map.values() if not command.is_test_feature]
        }
        self.help_message['embed']['fields'].sort(key=itemgetter('name'))

        # Info message begin.
        self.info_message = {
            'content': f'*Hello, I am **{self.name}**!*',
            'embed': {
                'description': f'A half-baked bot made by <@{self.AUTHOR_ID}>\n'
                               f'Written in awesome Python 3.7\n'
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
        await self.manager.run()
        await self.site.run()
        await self.client.run()

    async def on_message(self, client, data):
        if data['author'].get('bot', False):
            return

        channel_id = data['channel_id']
        channel = await self.get_channel(channel_id)
        if channel.type == Channel.TYPE_DM:
            msg = data['content']
            args = msg.split()
            if len(args) == 0:
                return
            args[0] = args[0].lower()
            await self.run_command_from_map(self.dm_channel_command_map, args, client, data)
            return

        if self.allowed_channels is None or channel_id in self.allowed_channels:
            msg = data['content']
            args = msg.lower().split()
            if len(args) < 2 or args[0] not in self.triggers and args[0] != f'<@{client.user["id"]}>':
                return
            await self.run_command_from_map(self.guild_channel_command_map, args[1:], client, data)
            return

        logger.info(f'Ignoring message from channel {channel_id}')

    async def run_command_from_map(self, command_map, args, client, data):
        command = command_map.get(args[0])
        if command is None:
            logger.info(f'Unsupported command {args}')
            return

        try:
            await command.execute(args[1:], self, client, data)
        except Command.IncorrectUsageException:
            logger.info(f'IncorrectUsageException: {args}')
        return

    async def get_channel(self, channel_id):
        channel = self.manager.get_channel(channel_id)
        if channel is None:
            channel = await self.client.get_channel(channel_id)
            channel = Channel.from_dict(channel)
            await self.manager.save_channel(channel)
        return channel
