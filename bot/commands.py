import copy
import logging
import time
from datetime import datetime, timedelta

from . import command, paginator

logger = logging.getLogger(__name__)


@command.command(desc='Responds with boop')
async def beep(bot, args, message):
    command.assert_arglen(args, 0, cmd=message.content)
    reply = {'content': '*boop*'}
    await bot.client.send_message(reply, message.channel_id)


@command.command(usage='help [cmd]',
                 desc='Displays information about commands. When `cmd` is provided, only displays '
                      'information about that command')
async def help(bot, args, message):
    if not args:
        reply = bot.help_message
        await paginator.paginate_and_send(reply, bot, message.channel_id, per_page=4,
                                          time_active=15 * 60, time_delay=2 * 60)
    else:
        command.assert_arglen(args, 1, cmd=message.content)
        cmd_name = args.pop()
        cmd = bot.command_map.get(cmd_name)
        command.assert_not_none(cmd, msg=f'Unrecognized command "{cmd_name}"', cmd=message.content)
        field = cmd.embed_field_rep()
        field['name'] = 'Usage: ' + field['name']
        reply = {
            'embed': {
                'title': cmd_name,
                'fields': [field],
            }
        }
        await bot.client.send_message(reply, message.channel_id)


@command.command(desc='Displays bot info')
async def info(bot, args, message):
    command.assert_arglen(args, 0, cmd=message.content)
    reply = bot.info_message
    await bot.client.send_message(reply, message.channel_id)


@command.command(usage='next [cnt] [at] [cc] [cf] [px]',
                 desc='Displays future contests. If `cnt` is absent, displays the next contest. '
                      'If `all`, displays all upcoming contests. If `day`, displays contests '
                      'which start within the next 24 hours. Optional site filters can be used, '
                      'where `at` = *AtCoder*, `cc` = *CodeChef* and `cf` = *Codeforces*')
async def next(bot, args, message):
    args = [arg.lower() for arg in args]
    site_tag_to_name = {}
    cnt = None
    for arg in args:
        name = bot.site_container.get_site_name(arg)
        if name is not None:
            site_tag_to_name[arg] = name
        elif arg in ('all', 'day'):
            command.assert_none(cnt, msg='More than 1 cnt argument', cmd=message.content)
            cnt = arg
        else:
            raise command.IncorrectUsageException(msg=f'Unrecognized argument "{arg}"', cmd=message.content)
    cnt = cnt or 1

    if cnt == 'day':
        start_max = datetime.now().timestamp() + timedelta(days=1).total_seconds()
        contests = bot.site_container.get_future_contests_before(start_max, site_tag_to_name.keys())
        logger.info(f'{len(contests)} contests fetched before {start_max}')
    else:
        contests = bot.site_container.get_future_contests_cnt(cnt, site_tag_to_name.keys())
        logger.info(f'{len(contests)} contests fetched out of {cnt}')

    if contests:
        reply = create_message_from_contests(contests, cnt, site_tag_to_name.values(), bot.TIMEZONE)
        await paginator.paginate_and_send(reply, bot, message.channel_id, per_page=bot.CONTESTS_PER_PAGE,
                                          time_active=15 * 60, time_delay=2 * 60)
    else:
        reply = {'content': '*No contest found*'}
        await bot.client.send_message(reply, message.channel_id)


def create_message_from_contests(contests, cnt, site_names, bot_timezone):
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

    message = {
        'content': f'*{title}*',
        'embed': embed,
    }
    return message


@command.command(desc='Displays bot status')
async def status(bot, args, message):
    command.assert_arglen(args, 0, cmd=message.content)
    reply = copy.deepcopy(bot.status_message)
    now = time.time()
    uptime = (now - bot.client.start_time) / 3600
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
    await bot.client.send_message(reply, message.channel_id)


@command.command(usage='sub at|cc|cf handle',
                 desc='Subscribe to rating changes. DM only. Experimental feature',
                 allow_guild=False, allow_dm=True)
async def sub(bot, args, message):
    command.assert_arglen(args, 2, cmd=message.content)
    user_id = message.author.id
    site_tag = args[0].lower()
    site_name = bot.site_container.get_site_name(site_tag)
    command.assert_not_none(site_name, msg='Unrecognized site', cmd=message.content)

    await bot.client.trigger_typing(message.channel_id)
    handle = args[1]
    profile = await bot.site_container.fetch_profile(handle, site_tag=site_tag)
    if profile is None:
        reply = {'content': '*No user found with given handle*'}
        await bot.client.send_message(reply, message.channel_id)
        return

    bot.entity_manager.create_user(user_id, message.channel_id)
    await bot.entity_manager.update_user_site_profile(user_id, profile)
    embed = bot.entity_manager.get_user(user_id).get_profile_embed(site_tag)
    reply = {
        'content': '*Your profile has been registered*',
        'embed': embed,
    }
    await bot.client.send_message(reply, message.channel_id)


@command.command(usage='unsub at|cc|cf',
                 desc='Unsubscribe from rating changes. DM only. Experimental feature',
                 allow_guild=False, allow_dm=True)
async def unsub(bot, args, message):
    command.assert_arglen(args, 1, cmd=message.content)
    user_id = message.author.id
    site_tag = args[0].lower()
    site_name = bot.site_container.get_site_name(site_tag)
    command.assert_not_none(site_name, msg='Unrecognized site', cmd=message.content)
    user = bot.entity_manager.get_user(user_id)
    if user is None:
        reply = {'content': f'*You are not subscribed to {site_name}*'}
        await bot.client.send_message(reply, message.channel_id)
        return
    profile = bot.entity_manager.get_user(user_id).get_profile_for_site(site_tag)
    if profile is None:
        reply = {'content': f'*You are not subscribed to {site_name}*'}
        await bot.client.send_message(reply, message.channel_id)
        return

    await bot.entity_manager.delete_user_site_profile(user_id, site_tag)
    reply = {'content': f'*You are now unsubscribed from {site_name}*'}
    await bot.client.send_message(reply, message.channel_id)
