import json
from datetime import datetime, timedelta
import asyncio
import aiohttp
import discord_opcode as d_op
import cfbot

class CPBot:

    API_URL = 'https://discordapp.com/api'
    CODEFORCES_CONTESTS_URL = 'http://codeforces.com/contests/'

    def __init__(self, token, bot_id, cf_bot=None, triggers=None, name='Bot', allowed_channels=None):
        self.token = token
        self.bot_id = bot_id
        self.triggers = triggers if triggers is not None else []
        self.name = name
        self.headers = {
            'Authorization': f'Bot {self.token}',
            'User-Agent': self.name,
        }
        self.last_seq = None
        self.cf_bot = cfbot.CFBot() if cf_bot is None else cf_bot
        self.allowed_channels = allowed_channels
        self.help_message = self.create_help_message()


    def create_help_message(self):
        msg = f'*Hello, I am **{self.name}**!*\n'
        if not self.triggers:
            trigger_line = '*Activate me by @mentioning me.*\n'
        else:
            trigger_line = f'*Activate me by @mentioning me or use my trigger* `{self.triggers[0]}`.\n'
        msg += trigger_line
        msg += 'Supported commands:\n' \
        '```beep         Responds "boop".\n' \
        'cfnext [x]   Displays the next x CF contests, x can be a\n' \
        '             positive integer or "all", defaults to 1.\n' \
        'help         Displays this message.```'
        return msg


    async def run(self):
        await self.cf_bot.init()
        resp = await self.request('GET', '/gateway')
        socket_url = resp['url']
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(f'{socket_url}?v=6&encoding=json') as ws:
                print('Websocket connected')
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.ERROR:
                        print('ERROR!', msg.data)
                        break
                    elif msg.type == aiohttp.WSMsgType.TEXT:
                        await self.handle_message(ws, msg.data)
                    else:
                        print(msg.type, msg.data)


    async def request(self, method, path, headers=None, json=None):
        if headers is None:
            headers = self.headers
        async with aiohttp.request(method, f'{self.API_URL}{path}', headers=headers, json=json) as response:
            assert response.status == 200, response.reason
            return await response.json()


    async def handle_message(self, ws, msg):
        msg = json.loads(msg)
        op = msg['op']
        if msg.get('s', None):
            self.last_seq = msg['s']
        typ = msg.get('t', None)
        data = msg.get('d', None)
        print('Received:', op, typ)
        if op == d_op.HELLO:
            print(data)
            reply = {
                'op': d_op.IDENTIFY,
                'd': {
                    'token': self.token,
                    'properties': {}
                }
            }
            await ws.send_json(reply)
            asyncio.ensure_future(self.heartbeat(ws, data['heartbeat_interval']))
        elif op == d_op.HEARTBEAT_ACK:
            print('Heartbeat-ack')
        elif op == d_op.DISPATCH:
            print('Handling dispatch')
            asyncio.ensure_future(self.handle_dispatch(typ, data))
        else:
            print('Did not handle opcode with data:')
            pretty = json.dumps(data, indent=2, sort_keys=True)
            print(pretty)


    async def heartbeat(self, ws, interval_ms):
        interval_sec = interval_ms / 1000
        data = {'op': d_op.HEARTBEAT}
        while True:
            await asyncio.sleep(interval_sec)
            data['d'] = self.last_seq
            print('Sending heartbeat', self.last_seq)
            await ws.send_json(data)


    async def handle_dispatch(self, typ, data):
        if typ == 'MESSAGE_CREATE':
            await self.on_message(data)
        else:
            # nothing else supported
            pass
            

    async def on_message(self, data):
        channel_id = data['channel_id']
        if self.allowed_channels is not None and channel_id not in self.allowed_channels:
            return
        msg = data['content']
        args = msg.split()
        if len(args) < 2 or args[0] not in self.triggers and args[0] != f'<@{self.bot_id}>':
            return

        args[1] = args[1].lower()
        if args[1] == 'help':
            reply = {'content': self.help_message}
            await self.send_message(reply, channel_id)
        elif args[1] == 'beep':
            reply = {'content': 'boop'}
            await self.send_message(reply, channel_id)
        elif args[1] == 'cfnext':
            try:
                cnt = args[2].lower()
                if cnt != 'all':
                    try:
                        cnt = int(cnt)
                        if cnt <= 0:
                            return
                    except:
                        return
            except:
                cnt = 1
            future_contests = self.cf_bot.get_future_contests(cnt)
            print(len(future_contests), 'future contests fetched out of', cnt)
            reply = self.create_message_from_contests(future_contests)
            await self.send_message(reply, channel_id)
        else:
            print('Unsupported command', args)


    def create_message_from_contests(self, contests):
        fields = []
        for contest in contests:
            start = datetime.fromtimestamp(contest['startTimeSeconds'])
            start = start.strftime('%d %b %y, %H:%M')
            duration_hrs, duration_secs = divmod(contest['durationSeconds'], 3600)
            duration_mins, duration_secs = divmod(duration_secs, 60)
            duration = f'{duration_hrs}h {duration_mins}m'
            url = self.CODEFORCES_CONTESTS_URL + str(contest['id'])

            combined = f'`{start}\u2001|\u2001{duration}\u2001|\u2001`[`link \u25F3`]({url} "Link to contest page")'
            field = {
                'name': contest['name'],
                'value': combined,
            }
            fields.append(field)

        if len(contests) == 1:
            title = 'Next Codeforces contest'
        else:
            title = f'Next {len(contests)} Codeforces contests'

        message = {
            'content': title,
            'embed': {
                'fields': fields,
            },
        }
        return message


    async def send_message(self, message, channel_id):
        print('Replying to channel', channel_id)
        await self.request('POST', f'/channels/{channel_id}/messages', json=message)
