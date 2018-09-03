import asyncio
import logging

logger = logging.getLogger(__name__)


class Fetcher:

    def __init__(self, refresh_interval=600):
        self.future_contests = None
        self.refresh_interval = refresh_interval
        self.last_fetched = None

    def get_future_contests(self, cnt):
        if cnt == 'all':
            return self.future_contests[:]
        return self.future_contests[:cnt]

    async def run(self):
        # inital fetch
        await self.update()
        # schedule for future
        asyncio.ensure_future(self.updater_task())

    async def update(self):
        raise NotImplementedError('This method must be overriden')

    async def updater_task(self):
        while True:
            try:
                await asyncio.sleep(self.refresh_interval)
                await self.update()
            except Exception as ex:
                logger.warning(f'Exception in fetching: {ex}')
