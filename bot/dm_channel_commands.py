from .command import command, assert_arglen, assert_true


@command(usage='sub at|cc|cf handle',
         desc='Subscribe to rating changes. DM only. Experimental feature')
async def sub(args, bot, client, message):
    assert_arglen(args, 2)
    user_id = message.author.id
    site_tag = args[0].lower()
    site_name = bot.site_container.get_site_name(site_tag)
    assert_true(site_name is not None)

    await bot.client.trigger_typing(message.channel_id)
    handle = args[1]
    profile = await bot.site_container.fetch_profile(handle, site_tag=site_tag)
    if profile is None:
        reply = {'content': '*No user found with given handle*'}
        await client.send_message(reply, message.channel_id)
        return

    bot.manager.create_user(user_id, message.channel_id)
    await bot.manager.update_user_site_profile(user_id, profile)
    desc = f'Name: {profile.name}\n' if profile.name is not None else ''
    desc += f'Rating: {profile.rating if profile.rating is not None else "Unrated"}'
    reply = {
        'content': '*Your profile has been registered*',
        'embed': {
            'title': f'{handle} on {site_name}',
            'url': profile.url,
            'description': desc,
        },
    }
    await client.send_message(reply, message.channel_id)


@command(usage='unsub at|cc|cf',
         desc='Unsubscribe from rating changes. DM only. Experimental feature')
async def unsub(args, bot, client, message):
    assert_arglen(args, 1)
    user_id = message.author.id
    site_tag = args[0].lower()
    site_name = bot.site_container.get_site_name(site_tag)
    assert_true(site_name is not None)
    user = bot.manager.get_user(user_id)
    if user is None:
        reply = {'content': f'*You are not subscribed to {site_name}*'}
        await client.send_message(reply, message.channel_id)
        return
    profile = bot.manager.get_user(user_id).get_profile_for_site(site_tag)
    if profile is None:
        reply = {'content': f'*You are not subscribed to {site_name}*'}
        await client.send_message(reply, message.channel_id)
        return

    await bot.manager.delete_user_site_profile(user_id, site_tag)
    reply = {'content': f'*You are now unsubscribed from {site_name}*'}
    await client.send_message(reply, message.channel_id)
