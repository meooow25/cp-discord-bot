import logging
import platform
from datetime import timedelta, timezone
from operator import itemgetter

from . import all_commands
from .command import Command
from contests.codeforces_fetcher import CodeforcesFetcher
from contests.codechef_fetcher import CodeChefFetcher
from contests.composite_fetcher import CompositeFetcher
from discord.client import Client

logger = logging.getLogger(__name__)


class Bot:
    MSG_MAX_CONTESTS = 6
    # TODO: Support separate time zones per channel or server
    TIME_ZONE = timezone(timedelta(hours=5, minutes=30))

    def __init__(self, token, name='Bot', activity_name=None, author_id=None, triggers=None, allowed_channels=None):
        self.name = name
        self.author_id = author_id
        self.triggers = triggers
        self.allowed_channels = allowed_channels

        self.client = Client(token, name=name, activity_name=activity_name, on_message=self.on_message)
        self.fetcher = CompositeFetcher([CodeforcesFetcher(), CodeChefFetcher()])
        self.command_map = {}
        for attr_name in dir(all_commands):
            attr = getattr(all_commands, attr_name)
            if isinstance(attr, Command):
                command = attr
                self.command_map[command.name] = command
        logger.info(f'Loaded commands: {self.command_map.keys()}')

        self.help_message = {}
        if not triggers:
            self.help_message['content'] = '*@mention me to activate me.*\n'
        else:
            self.help_message['content'] = f'*@mention me or use my trigger `{self.triggers[0]}` to activate me.*\n'
        self.help_message['embed'] = {
            'title': 'Supported commands:',
            'fields': [{
                'name': f'`{command.usage}`',
                'value': command.desc
            } for command in self.command_map.values()]
        }
        self.help_message['embed']['fields'].sort(key=itemgetter('name'))

        self.info_message = {
            'embed': {
                'title': f'*Hello, I am **{self.name}**!*',
                'description': f'*A half-baked bot made by <@{self.author_id}>\n'
                               f'Written in awesome Python {platform.python_version()}\n'
                               f'Running on {platform.system()}-{platform.release()} like a boss*',
            },
        }

    async def run(self):
        await self.fetcher.run()
        await self.client.run()

    async def on_message(self, client, data):
        channel_id = data['channel_id']
        if self.allowed_channels is not None and channel_id not in self.allowed_channels:
            return
        msg = data['content']
        args = msg.lower().split()
        if len(args) < 2 or args[0] not in self.triggers and args[0] != f'<@{client.user["id"]}>':
            return

        command = self.command_map.get(args[1])
        if command is None:
            logger.info(f'Unsupported command {args}')
            return

        try:
            await command.execute(args[2:], self, client, data)
        except Command.IncorrectUsageException:
            logger.info(f'IncorrectUsageException: {args}')
