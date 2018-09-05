import logging
import platform
import time
from datetime import datetime

from contests.codeforces_fetcher import CodeforcesFetcher
from contests.codechef_fetcher import CodeChefFetcher
from contests.composite_fetcher import CompositeFetcher
from discord.client import Client

logger = logging.getLogger(__name__)


class Bot:
    MSG_MAX_CONTESTS = 6

    def __init__(self, token, name='Bot', activity_name=None, author_id=None, triggers=None, allowed_channels=None):
        self.name = name
        self.author_id = author_id
        self.triggers = triggers
        self.allowed_channels = allowed_channels

        self.client = Client(token, name=name, activity_name=activity_name, on_message=self.on_message)
        self.fetcher = CompositeFetcher([CodeforcesFetcher(), CodeChefFetcher()])

        self.help_message = {}
        if not triggers:
            self.help_message['content'] = '*@mention me to activate me.*\n'
        else:
            self.help_message['content'] = f'*@mention me or use my trigger* `{self.triggers[0]}` *to activate me.*\n'
        self.help_message['embed'] = {
            'title': 'Supported commands:',
            'fields': [
                {
                    'name': '`beep`',
                    'value': 'Responds with `boop`',
                },
                {
                    'name': '`help`',
                    'value': 'Displays this message',
                },
                {
                    'name': '`info`',
                    'value': 'Displays bot info',
                },
                {
                    'name': '`next [count] [**sites]`',
                    'value': 'Gets the next `count` contests, defaults to `1`. Takes optional site filters which '
                             'may be `cc` for *CodeChef* or `cf` for *Codeforces*',
                },
            ],
        }

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

        arglen = len(args)
        args[1] = args[1].lower()
        if arglen == 2 and args[1] == 'help':
            reply = self.help_message
            await client.send_message(reply, channel_id)
        elif arglen == 2 and args[1] == 'beep':
            reply = {'content': 'boop'}
            await client.send_message(reply, channel_id)
        elif arglen == 2 and args[1] == 'info':
            reply = dict(self.info_message)
            now = time.time()
            uptime = (now - client.start_time) / 3600
            field1 = {
                'name': 'Bot uptime:',
                'value': f'Online since {uptime:.1f} hrs ago'
            }
            field2 = {
                'name': 'Last updated:',
                'value': '',
            }
            for f in self.fetcher.fetchers:
                last = (now - f.last_fetched) / 60
                field2['value'] += f'{f.SITE}: {last:.0f} mins ago\n'
            reply['embed']['fields'] = [field1, field2]
            await client.send_message(reply, channel_id)
        elif args[1] == 'next':
            params = args[2:]
            params.sort()
            cnt = None
            sitemap = {'cc': 'CodeChef', 'cf': 'Codeforces'}
            sites = set()
            for p in params:
                try:
                    p = int(p)
                    if cnt is not None or p <= 0:
                        return
                    cnt = p
                except ValueError:
                    if p == 'all':
                        cnt = p
                        continue
                    if p not in sitemap or p in sites:
                        return
                    sites.add(sitemap[p])
            if cnt is None:
                cnt = 1
            future_contests = self.fetcher.get_future_contests(cnt, sites)
            logger.info(f'{len(future_contests)} future contests fetched out of {cnt}')
            reply = self.create_message_from_contests(future_contests, sites)
            await client.send_message(reply, channel_id)
        else:
            logger.info(f'Unsupported command {args}')

    def create_message_from_contests(self, contests, sites):
        if len(contests) == 0:
            message = {
                'embed': {
                    'title': 'No contest found',
                },
            }
        else:
            num_hidden = len(contests) - self.MSG_MAX_CONTESTS
            contests = contests[:self.MSG_MAX_CONTESTS]
            descs = []
            for contest in contests:
                start = datetime.fromtimestamp(contest.start)
                start = start.strftime('%d %b %y, %H:%M')

                duration_days, duration_secs = divmod(contest.length, 60 * 60 * 24)
                duration_hrs, duration_secs = divmod(duration_secs, 60 * 60)
                duration_mins, duration_secs = divmod(duration_secs, 60)
                duration = f'{duration_hrs}h {duration_mins}m'
                if duration_days > 0:
                    duration = f'{duration_days}d ' + duration

                url = contest.url

                descs.append((contest.name, contest.site, start, duration, url))

            max_site_len = max(len(desc[1]) for desc in descs)
            max_duration_len = max(len(desc[3]) for desc in descs)
            em = '\u2001'

            def make_field(d):
                return {
                    'name': d[0],
                    'value': f'`{d[1].ljust(max_site_len, em)}{em}|'
                             f'{em}{d[2]}{em}|'
                             f'{em}{d[3].rjust(max_duration_len, em)}{em}|'
                             f'{em}`[`link \u25F3`]({d[4]} "Link to contest page")'
                }

            title = 'Next contest' if len(contests) == 1 else f'Next {len(contests)} contests'
            fields = [make_field(desc) for desc in descs]
            message = {
                'content': title,
                'embed': {
                    'fields': fields,
                },
            }
            if num_hidden > 0:
                message['embed']['footer'] = {
                    'text': f'{num_hidden} more contest{"s" if num_hidden > 1 else ""} not displayed'
                }

        if sites:
            message['embed']['description'] = 'Showing only: ' + ', '.join(site for site in sites)

        return message
