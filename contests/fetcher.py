import asyncio
import logging
import time

logger = logging.getLogger(__name__)


class Fetcher:

    def __init__(self, refresh_interval=600):
        self.future_contests = None
        self.refresh_interval = refresh_interval
        self.last_fetched = None

    @staticmethod
    def filter_by_site(sites):
        if not sites:
            return lambda contest: True
        return lambda contest: contest.site in sites

    @staticmethod
    def filter_by_start(start_max):
        return lambda contest: contest.start <= start_max

    def get_future_contests_cnt(self, cnt, sites):
        logger.info(f'get_future_contests_cnt: {cnt} {sites}')
        filtered_by_site = filter(self.filter_by_site(sites), self.future_contests)
        if cnt == 'all':
            cnt = len(self.future_contests)
        return list(filtered_by_site)[:cnt]

    def get_future_contests_before(self, start_max, sites):
        filtered_by_site = filter(self.filter_by_site(sites), self.future_contests)
        filtered_by_start = filter(self.filter_by_start(start_max), filtered_by_site)
        return list(filtered_by_start)

    async def run(self):
        # Initial fetch.
        await self.update()
        # Schedule for future
        asyncio.create_task(self.updater_task())

    def update_last_fetched(self):
        self.last_fetched = time.time()

    async def update(self):
        raise NotImplementedError('This method must be overridden')

    async def updater_task(self):
        while True:
            try:
                await asyncio.sleep(self.refresh_interval)
                await self.update()
            except asyncio.CancelledError:
                logger.info('Received CancelledError, stopping task')
                break
            except Exception as ex:
                logger.warning(f'Exception in fetching: {ex}, continuing regardless')
