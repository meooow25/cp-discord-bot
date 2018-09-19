import logging
import time
from datetime import datetime, timezone, timedelta

from .command import Command, command

logger = logging.getLogger(__name__)


def assert_true(arg):
    if not arg:
        raise Command.IncorrectUsageException()


def assert_arglen(args, num):
    if len(args) != num:
        raise Command.IncorrectUsageException()


@command(desc='Responds with boop')
async def beep(args, bot, client, data):
    assert_arglen(args, 0)
    reply = {'content': '*boop*'}
    await client.send_message(reply, data['channel_id'])


@command(desc='Displays this message')
async def help(args, bot, client, data):
    assert_arglen(args, 0)
    reply = bot.help_message
    await client.send_message(reply, data['channel_id'])


@command(desc='Displays bot info')
async def info(args, bot, client, data):
    assert_arglen(args, 0)
    reply = bot.info_message
    await client.send_message(reply, data['channel_id'])


@command(usage='next [cnt] [at] [cc] [cf]',
         desc='Displays future contests. If cnt is `all` or an integer, displays next `cnt` contests. '
              'If `cnt` is `day`, displays contests which start within the next 24 hours. If `cnt` is '
              'missing, it defaults to `1`. Takes optional site filters, where `at` = AtCoder, `cc` = *CodeChef* '
              'and `cf` = *Codeforces*')
async def next(args, bot, client, data):
    sitemap = {
        'at': 'AtCoder',
        'cc': 'CodeChef',
        'cf': 'Codeforces',
    }

    opt = set()
    rem = set()
    for arg in args:
        if arg in sitemap:
            opt.add(arg)
        else:
            rem.add(arg)

    if len(rem) == 0:
        cnt = 1
    elif len(rem) == 1:
        cnt = rem.pop()
        if cnt == 'all' or cnt == 'day':
            pass
        else:
            try:
                cnt = int(cnt)
                assert_true(cnt > 0)
            except ValueError:
                raise Command.IncorrectUsageException()
    else:
        raise Command.IncorrectUsageException()

    sites = [sitemap[arg] for arg in opt]
    sites.sort()
    if cnt == 'day':
        start_max = datetime.now(timezone.utc).timestamp() + timedelta(days=1).total_seconds()
        future_contests = bot.fetcher.get_future_contests_before(start_max, sites)
        logger.info(f'{len(future_contests)} future contests fetched before {start_max}')
    else:
        future_contests = bot.fetcher.get_future_contests_cnt(cnt, sites)
        logger.info(f'{len(future_contests)} future contests fetched out of {cnt}')

    reply = create_message_from_contests(future_contests, cnt, sites, bot.MSG_MAX_CONTESTS, bot.TIME_ZONE)
    await client.send_message(reply, data['channel_id'])


def create_message_from_contests(contests, cnt, sites, max_contests, time_zone):
    if len(contests) == 0:
        message = {'content': '*No contest found*'}
        return message

    num_hidden = len(contests) - max_contests
    contests = contests[:max_contests]
    descs = []
    for contest in contests:
        start = datetime.fromtimestamp(contest.start, timezone.utc).astimezone(time_zone)
        start = start.strftime('%d %b %y, %H:%M')

        duration_days, rem_secs = divmod(contest.length, 60 * 60 * 24)
        duration_hrs, rem_secs = divmod(rem_secs, 60 * 60)
        duration_mins, rem_secs = divmod(rem_secs, 60)
        duration = f'{duration_hrs}h {duration_mins}m'
        if duration_days > 0:
            duration = f'{duration_days}d ' + duration

        descs.append((contest.name, contest.site, start, duration, contest.url))

    max_site_len = max(len(desc[1]) for desc in descs)
    max_duration_len = max(len(desc[3]) for desc in descs)
    em = '\u2001'

    def make_field(name, site, start, duration, url):
        return {
            'name': name,
            'value': f'`{site.ljust(max_site_len, em)}{em}|'
                     f'{em}{start}{em}|'
                     f'{em}{duration.rjust(max_duration_len, em)}{em}|'
                     f'{em}`[`link \u25F3`]({url} "Link to contest page")'
        }

    if cnt == 'day':
        title = 'Contests that start under 24 hours from now'
    else:
        title = 'Next contest' if len(contests) == 1 else f'Next {len(contests)} contests'
    title = f'*{title}*'
    fields = [make_field(*desc) for desc in descs]
    message = {
        'content': title,
        'embed': {
            'fields': fields,
        },
    }
    if num_hidden > 0:
        # TODO: Add pagination support
        message['embed']['footer'] = {
            'text': f'{num_hidden} more contest{"s" if num_hidden > 1 else ""} not displayed'
        }

    if sites:
        message['embed']['description'] = 'Showing only: ' + ', '.join(site for site in sites)

    return message


@command(desc='Displays bot status')
async def status(args, bot, client, data):
    assert_arglen(args, 0)
    reply = dict(bot.status_message)
    now = time.time()
    uptime = (now - client.start_time) / 3600
    field1 = {
        'name': 'Bot Uptime',
        'value': f'Online since {uptime:.1f} hrs ago'
    }
    field2 = {
        'name': 'Last Updated',
        'value': '',
    }
    for f in bot.fetcher.fetchers:
        last = (now - f.last_fetched) / 60
        field2['value'] += f'{f.SITE}: {last:.0f} mins ago\n'
    reply['embed']['fields'] += [field1, field2]
    await client.send_message(reply, data['channel_id'])
