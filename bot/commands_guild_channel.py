import copy
import logging
import time
from datetime import datetime, timezone, timedelta

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


@command(usage='next [cnt] [at] [cc] [cf]',
         desc='Displays future contests. If cnt is `all` or an integer, displays next `cnt` contests. '
              'If `cnt` is `day`, displays contests which start within the next 24 hours. If `cnt` is '
              'missing, it defaults to `1`. Takes optional site filters, where `at` = *AtCoder*, `cc` '
              '= *CodeChef* and `cf` = *Codeforces*')
async def next(args, bot, client, message):
    args = [arg.lower() for arg in args]
    site_tag_to_name = {}
    rem = set()
    for arg in args:
        name = bot.site_container.get_site_name(arg)
        if name is not None:
            site_tag_to_name[arg] = name
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
                Command.assert_true(cnt > 0)
            except ValueError:
                raise Command.IncorrectUsageException()
    else:
        raise Command.IncorrectUsageException()

    if cnt == 'day':
        start_max = datetime.now(timezone.utc).timestamp() + timedelta(days=1).total_seconds()
        future_contests = bot.site_container.get_future_contests_before(start_max, site_tag_to_name.keys())
        logger.info(f'{len(future_contests)} future contests fetched before {start_max}')
    else:
        future_contests = bot.site_container.get_future_contests_cnt(cnt, site_tag_to_name.keys())
        logger.info(f'{len(future_contests)} future contests fetched out of {cnt}')

    reply = create_message_from_contests(future_contests, cnt, site_tag_to_name.values(),
                                         bot.MSG_MAX_CONTESTS, bot.TIME_ZONE)
    await client.send_message(reply, message.channel_id)


def create_message_from_contests(contests, cnt, site_names, max_contests, time_zone):
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
        title = 'Next contest' if len(contests) == 1 else f'Next {len(contests)} contests'
    fields = [make_field(*desc) for desc in descs]
    message = {
        'content': f'*{title}*',
        'embed': {
            'fields': fields,
        },
    }
    if num_hidden > 0:
        plural = 's' if num_hidden > 1 else ''
        # TODO: Add pagination support
        message['embed']['footer'] = {
            'text': f'{num_hidden} more contest{plural} not displayed'
        }

    if site_names:
        message['embed']['description'] = 'Showing only: ' + ', '.join(name for name in site_names)

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
