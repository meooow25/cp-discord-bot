import asyncio
import cpbot

TOKEN = 'token'
BOT_ID = 'id'
NAME = 'CPBot'
TRIGGERS = ['trigger']
CHANNELS = ['channel']

def main():
    bot = cpbot.CPBot(TOKEN, BOT_ID, name=NAME, triggers=TRIGGERS, allowed_channels=CHANNELS)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(bot.run())

if __name__ == '__main__':
    main()
