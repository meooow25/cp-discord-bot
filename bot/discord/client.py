import asyncio
import json
import logging
import platform
import time
from enum import IntEnum

import aiohttp

from .models import Channel, Message


class Opcode(IntEnum):
    DISPATCH = 0
    HEARTBEAT = 1
    IDENTIFY = 2
    STATUS_UPDATE = 3
    VOICE_STATE_UPDATE = 4
    RESUME = 6
    RECONNECT = 7
    REQUEST_GUILD_MEMBERS = 8
    INVALID_SESSION = 9
    HELLO = 10
    HEARTBEAT_ACK = 11


class EventType:
    # This list is not exhaustive.
    READY = 'READY'
    CHANNEL_CREATE = 'CHANNEL_CREATE'
    CHANNEL_UPDATE = 'CHANNEL_UPDATE'
    CHANNEL_DELETE = 'CHANNEL_DELETE'
    GUILD_CREATE = 'GUILD_CREATE'
    GUILD_UPDATE = 'GUILD_UPDATE'
    GUILD_DELETE = 'GUILD_DELETE'
    MESSAGE_CREATE = 'MESSAGE_CREATE'
    MESSAGE_UPDATE = 'MESSAGE_UPDATE'
    MESSAGE_DELETE = 'MESSAGE_DELETE'
    PRESENCE_UPDATE = 'PRESENCE_UPDATE'
    TYPING_START = 'TYPING_START'


class Client:
    API_URL = 'https://discordapp.com/api'

    def __init__(self, token, name='Bot', activity_name=None):
        self.token = token
        self.name = name
        self.headers = {
            'Authorization': f'Bot {self.token}',
            'User-Agent': self.name,
        }
        self.activity_name = activity_name

        self.on_message = None
        self.user = None
        self.start_time = None
        self.last_seq = None
        self.logger = logging.getLogger(self.__class__.__qualname__)

    async def run(self, *, on_message):
        """Connect to Discord and run forever."""
        self.on_message = on_message
        resp = await self._request('GET', '/gateway')
        socket_url = resp['url']
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(f'{socket_url}?v=6&encoding=json') as ws:
                self.start_time = time.time()
                self.logger.info('Websocket connected')
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.CLOSE:
                        self.logger.error(f'Discord closed the connection: {msg.data}, {msg.extra}')
                        raise Exception(f'Websocket closed')
                    if msg.type == aiohttp.WSMsgType.ERROR:
                        self.logger.error(f'Websocket error response: {msg.data}')
                        raise Exception(f'Websocket error')
                    elif msg.type == aiohttp.WSMsgType.TEXT:
                        await self._handle_message(ws, msg.data)
                    else:
                        self.logger.warning(f'Unhandled type: {msg.type}, {msg.data}')
        raise Exception('Discord websocket disconnected')

    async def _request(self, method, path, headers=None, json_data=None, expect_json=True):
        """Send a HTTP request to the Discord API."""
        headers = headers or self.headers
        self.logger.debug(f'Request: {method} {path} {headers} {json_data}')
        async with aiohttp.request(method, f'{self.API_URL}{path}', headers=headers, json=json_data) as response:
            # TODO: Implement a way of ensuring rate limits
            response.raise_for_status()
            if expect_json:
                return await response.json()

    async def _handle_message(self, ws, msg):
        """Handle a websocket message."""
        msg = json.loads(msg)
        op = msg['op']
        if msg.get('s'):
            self.last_seq = msg['s']
        typ = msg.get('t')
        data = msg.get('d')
        self.logger.info(f'Received: {op} {typ}')
        if op == Opcode.HELLO:
            self.logger.info(data)
            reply = {
                'op': Opcode.IDENTIFY,
                'd': {
                    'token': self.token,
                    'properties': {
                        '$os': platform.platform(terse=1),
                    },
                    'compress': False,
                },
            }
            if self.activity_name:
                reply['d']['presence'] = {
                    'game': {
                        'name': self.activity_name,
                        'type': 0,
                    },
                    'status': 'online',
                    'since': None,
                    'afk': False,
                }
            await ws.send_json(reply)
            asyncio.create_task(self._heartbeat_task(ws, data['heartbeat_interval']))
        elif op == Opcode.HEARTBEAT_ACK:
            self.logger.info('Heartbeat-ack received')
        elif op == Opcode.DISPATCH:
            self.logger.debug('Handling dispatch')
            await self._handle_dispatch(typ, data)
        else:
            self.logger.info(f'Did not handle opcode with data: {data}')

    async def _heartbeat_task(self, ws, interval_ms):
        """Run forever, send a heartbeat through the websocket ``ws`` every ``interval_ms`` milliseconds."""
        interval_sec = interval_ms / 1000
        data = {'op': Opcode.HEARTBEAT}
        while True:
            await asyncio.sleep(interval_sec)
            data['d'] = self.last_seq
            self.logger.info(f'Sending heartbeat {self.last_seq}')
            await ws.send_json(data)

    async def _handle_dispatch(self, typ, data):
        """Handle a websocket dispatch event."""
        if typ == EventType.READY:
            self.user = data['user']
            self.logger.info(f'Self data: {self.user}')
        elif typ == EventType.MESSAGE_CREATE:
            if self.on_message:
                message = Message(**data)
                self.logger.debug('Calling on_message handler')
                # Run on_message as a separate coroutine.
                asyncio.create_task(self.on_message(self, message))
        else:
            # Nothing else supported.
            pass

    async def send_message(self, message, channel_id):
        """Send a message on Discord.

        :param message: the message as a dict.
        :param channel_id: the channel to send the message to.
        """
        self.logger.info(f'Replying to channel {channel_id}')
        await self._request('POST', f'/channels/{channel_id}/messages', json_data=message)

    async def get_channel(self, channel_id):
        """Get the channel object for the channel with given id."""
        self.logger.info(f'Getting channel with id: {channel_id}')
        channel_d = await self._request('GET', f'/channels/{channel_id}')
        return Channel(**channel_d)

    async def get_dm_channel(self, user_id):
        """Get the channel object for the DM channel with the user with given id."""
        self.logger.info(f'Getting DM channel for user: {user_id}')
        json_data = {'recipient_id': user_id}
        channel_d = await self._request('POST', '/users/@me/channels', json_data=json_data)
        return Channel(**channel_d)

    async def trigger_typing(self, channel_id):
        """Trigger the typing indicator on the channel with given id."""
        self.logger.info(f'Triggering typing on channel {channel_id}')
        return await self._request('POST', f'/channels/{channel_id}/typing', expect_json=False)
