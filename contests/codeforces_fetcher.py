import logging
import time

import aiohttp

from .fetcher import Fetcher
from .models import Contest

logger = logging.getLogger(__name__)


class CodeforcesFetcher(Fetcher):
    SITE = 'Codeforces'
    API_URL = 'http://codeforces.com/api'
    CONTESTS_URL = 'http://codeforces.com/contests'

    def __init__(self, refresh_interval=600):
        super().__init__(refresh_interval)

    async def run(self):
        logger.info(f'Setting up {self.SITE} fetcher...')
        await super().run()

    async def update(self):
        """Overrides update method in Fetcher"""
        data = await self.request('/contest.list', gym='false')
        assert data['status'] == 'OK', data['comment']
        contests = [contest for contest in data['result'] if contest['phase'] == 'BEFORE']
        self.future_contests = [Contest(contest['name'],
                                        self.SITE,
                                        f'{self.CONTESTS_URL}/{contest["id"]}',
                                        contest.get('startTimeSeconds'),
                                        contest['durationSeconds']) for contest in contests]
        # TODO: Consider how to handle contests with missing start
        self.future_contests = [contest for contest in self.future_contests if contest.start is not None]
        self.future_contests.sort()
        logger.info(f'Updated! {len(self.future_contests)} upcoming')
        logger.debug(f'Fetched contests: {self.future_contests}')
        self.last_fetched = time.time()

    async def request(self, path, **kwargs):
        logger.debug(f'GET {path} {kwargs}')
        async with aiohttp.request('GET', f'{self.API_URL}{path}', params=kwargs) as response:
            response.raise_for_status()
            return await response.json()
