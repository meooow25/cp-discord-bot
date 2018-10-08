import json
import logging
import platform
from datetime import timedelta, timezone
from operator import itemgetter

from discord.models import Channel
from . import guild_channel_commands, dm_channel_commands
from .command import Command


class Bot:
    AUTHOR_ID = 'author_id'
    GITHUB_URL = 'https://github.com/meooow25/cp-discord-bot'
    MSG_MAX_CONTESTS = 5
    # TODO: Support separate time zones per channel or server
    TIME_ZONE = timezone(timedelta(hours=5, minutes=30))

    def __init__(self, name, client, site_container, manager, triggers=None, allowed_channels=None):
        self.name = name
        self.client = client
        self.site_container = site_container
        self.manager = manager
        self.triggers = triggers
        self.allowed_channels = allowed_channels
        self.logger = logging.getLogger(self.__class__.__qualname__)

        self.guild_channel_command_map = {}
        for attr_name in dir(guild_channel_commands):
            attr = getattr(guild_channel_commands, attr_name)
            if isinstance(attr, Command):
                command = attr
                self.guild_channel_command_map[command.name] = command
        self.logger.info(f'Loaded guild channel commands: {self.guild_channel_command_map.keys()}')

        self.dm_channel_command_map = {}
        for attr_name in dir(dm_channel_commands):
            attr = getattr(dm_channel_commands, attr_name)
            if isinstance(attr, Command):
                command = attr
                self.dm_channel_command_map[command.name] = command
        self.logger.info(f'Loaded DM channel commands: {self.dm_channel_command_map.keys()}')

        # Help message begin.
        self.help_message = {}
        if not triggers:
            self.help_message['content'] = '*@mention me to activate me.*\n'
        else:
            self.help_message['content'] = f'*@mention me or use my trigger `{self.triggers[0]}` to activate me.*\n'

        guild_channel_fields = [{
            'name': f'{command.usage}',
            'value': command.desc,
        } for command in self.guild_channel_command_map.values() if not command.experimental]
        guild_channel_fields.sort(key=itemgetter('name'))
        dm_channel_fields = [{
            'name': f'{command.usage}',
            'value': command.desc,
        } for command in self.dm_channel_command_map.values() if not command.experimental]
        dm_channel_fields.sort(key=itemgetter('name'))
        self.help_message['embed'] = {
            'title': 'Supported commands:',
            'fields': guild_channel_fields + dm_channel_fields,
        }

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
        await self.site_container.run(
            get_all_users=self.get_all_users,
            on_profile_fetch=self.on_profile_fetch
        )
        await self.client.run(on_message=self.on_message)

    async def on_message(self, client, message):
        # message.author is None when message is sent by a webhook.
        if message.author and message.author.bot:
            return

        channel = await self.get_channel(message.channel_id)
        if channel.type == Channel.Type.DM:
            # Trigger not required for DM.
            args = message.content.split()
            if not args:
                return
            await self.run_command_from_map(self.dm_channel_command_map, args, client, message)
            return

        if self.allowed_channels is None or message.channel_id in self.allowed_channels:
            args = message.content.split()
            if len(args) < 2:
                # Trigger + command
                return
            # Ignore trigger case.
            args[0] = args[0].lower()
            if args[0] not in self.triggers and args[0] != f'<@{client.user["id"]}>':
                return
            await self.run_command_from_map(self.guild_channel_command_map, args[1:], client, message)
            return

        self.logger.info(f'Ignoring message from channel {message.channel_id}')

    async def run_command_from_map(self, command_map, args, client, message):
        # Ignore command case.
        args[0] = args[0].lower()
        command = command_map.get(args[0])
        if command is None:
            self.logger.info(f'Unsupported command {args}')
            return

        try:
            await command.execute(args[1:], self, client, message)
        except Command.IncorrectUsageException as ex:
            self.logger.info(f'IncorrectUsageException: {args}')
        return

    async def get_channel(self, channel_id):
        channel = self.manager.get_channel(channel_id)
        if channel is None:
            channel = await self.client.get_channel(channel_id)
            await self.manager.save_channel(channel)
        return channel

    def get_all_users(self):
        return self.manager.users[:]

    async def on_profile_fetch(self, user, old_profile, new_profile):
        changed = await self.manager.update_user_site_profile(user.discord_id, new_profile)
        if not changed:
            return
        self.logger.debug(f'Changed profile: {old_profile.to_dict()}, {new_profile.to_dict()}')
        old_str = f'Name: {old_profile.name}\n' if old_profile.name is not None else ''
        old_str += f'Rating: {old_profile.rating if old_profile.rating is not None else "Unrated"}'
        new_str = f'Name: {new_profile.name}\n' if new_profile.name is not None else ''
        new_str += f'Rating: {new_profile.rating if new_profile.rating is not None else "Unrated"}'
        fields = [
            {
                'name': 'Previous',
                'value': old_str,
                'inline': 'true',
            },
            {
                'name': 'Current',
                'value': new_str,
                'inline': 'true',
            },
        ]
        msg = {
            'content': '*Your profile has been updated*',
            'embed': {
                'title': f'{new_profile.handle} on {new_profile.site_name}',
                'url': new_profile.url,
                'fields': fields,
            },
        }
        await self.client.send_message(msg, user.dm_channel_id)
