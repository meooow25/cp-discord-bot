from .command import command, assert_arglen, assert_true


@command(is_test_feature=True)
async def sub(args, bot, client, data):
    assert_arglen(args, 2)
    site_map = {
        'at': 'AtCoder',
        'cc': 'CodeChef',
        'cf': 'Codeforces',
    }

    user_id = data['author']['id']
    assert_true(args[0] in site_map)
    site = site_map[args[0]]
    handle = args[1]
    profile = await bot.site.fetch_profile(site, handle)
    if profile is None:
        reply = {'content': 'User not found'}
        await client.send_message(reply, data['channel_id'])
        return

    await bot.manager.set_user_site_profile(user_id, profile)
    msg = str(profile.to_dict())
    reply = {'content': msg}
    await client.send_message(reply, data['channel_id'])
