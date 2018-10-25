import copy
import logging
import time
from datetime import datetime, timedelta

from . import paginator
from .command import Command, command

logger = logging.getLogger(__name__)


@command(desc='Responds with boop')
async def beep(args, bot, client, message):
    Command.assert_arglen(args, 0)
    reply = {'content': '*boop*'}
    await client.send_message(reply, message.channel_id)


@command(desc='Displays this message')
async def help(args, bot, client, message):
    Command.assert_arglen(args, 0)
    reply = bot.help_message
    await client.send_message(reply, message.channel_id)


@command(desc='Displays bot info')
async def info(args, bot, client, message):
    Command.assert_arglen(args, 0)
    reply = bot.info_message
    await client.send_message(reply, message.channel_id)


@command(usage='next [cnt] [px] [at] [cc] [cf]',
         desc='Displays future contests. If `cnt` is absent, displays the next contest. If '
              '`all`, displays all upcoming contests. If `day`, displays contests which start '
              'within the next 24 hours. The `p` option specifies the page number, e.g `p2` or '
              '`p10`. Optional site filters can be used, where `at` = *AtCoder*, `cc` = '
              '*CodeChef* and `cf` = *Codeforces*')
async def next(args, bot, client, message):
    args = [arg.lower() for arg in args]
    site_tag_to_name = {}
    cnt = None
    page = None
    for arg in args:
        name = bot.site_container.get_site_name(arg)
        if name is not None:
            site_tag_to_name[arg] = name
        elif arg in ('all', 'day'):
            Command.assert_none(cnt)
            cnt = arg
        elif arg.startswith('p'):
            Command.assert_none(page)
            try:
                page = int(arg[1:])
                Command.assert_true(page > 0)
            except ValueError:
                raise Command.IncorrectUsageException()
        else:
            raise Command.IncorrectUsageException()

    cnt = cnt or 1
    page = page or 1

    if cnt == 'day':
        start_max = datetime.now().timestamp() + timedelta(days=1).total_seconds()
        contests = bot.site_container.get_future_contests_before(start_max, site_tag_to_name.keys())
        logger.info(f'{len(contests)} contests fetched before {start_max}')
    else:
        contests = bot.site_container.get_future_contests_cnt(cnt, site_tag_to_name.keys())
        logger.info(f'{len(contests)} contests fetched out of {cnt}')

    contests, page, num_pages = paginator.paginate(contests, bot.CONTESTS_PER_PAGE, page)

    reply = create_message_from_contests(contests, cnt, site_tag_to_name.values(),
                                         bot.TIMEZONE, page, num_pages)
    await client.send_message(reply, message.channel_id)


def create_message_from_contests(contests, cnt, site_names, bot_timezone, page, num_pages):
    if len(contests) == 0:
        message = {'content': '*No contest found*'}
        return message

    descs = []
    for contest in contests:
        start = datetime.fromtimestamp(contest.start, bot_timezone)
        start = start.strftime('%d %b %y, %H:%M')

        duration_days, rem_secs = divmod(contest.length, 60 * 60 * 24)
        duration_hrs, rem_secs = divmod(rem_secs, 60 * 60)
        duration_mins, rem_secs = divmod(rem_secs, 60)
        duration = f'{duration_hrs}h {duration_mins}m'
        if duration_days > 0:
            duration = f'{duration_days}d ' + duration

        descs.append((contest.name, contest.site_name, start, duration, contest.url))

    max_site_name_len = max(len(desc[1]) for desc in descs)
    max_duration_len = max(len(desc[3]) for desc in descs)
    em = '\u2001'

    def make_field(name, site_name, start, duration, url):
        return {
            'name': name,
            'value': f'`{site_name.ljust(max_site_name_len, em)}{em}|'
                     f'{em}{start}{em}|'
                     f'{em}{duration.rjust(max_duration_len, em)}{em}|'
                     f'{em}`[`link \u25F3`]({url} "Link to contest page")'
        }

    if cnt == 'day':
        title = 'Contests that start under 24 hours from now'
    else:
        title = 'Upcoming contests'
    embed = {
        'fields': [make_field(*desc) for desc in descs],
    }
    if site_names:
        embed['description'] = 'Showing only: ' + ', '.join(name for name in site_names)
    if num_pages > 1:
        embed['footer'] = {
            'text': f'Page {page} / {num_pages}',
        }

    message = {
        'content': f'*{title}*',
        'embed': embed,
    }
    return message


@command(desc='Displays bot status')
async def status(args, bot, client, message):
    Command.assert_arglen(args, 0)
    reply = copy.deepcopy(bot.status_message)
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
    # TODO: Shift the code below to a member function of Site.
    for site in bot.site_container.sites:
        last = (now - site.contests_last_fetched) / 60
        field2['value'] += f'{site.NAME}: {last:.0f} mins ago\n'
    reply['embed']['fields'] += [field1, field2]
    await client.send_message(reply, message.channel_id)
