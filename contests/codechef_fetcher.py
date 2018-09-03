
import logging
import time
from datetime import datetime

import aiohttp
from bs4 import BeautifulSoup

from .fetcher import Fetcher
from .models import Contest

logger = logging.getLogger(__name__)


class CodeChefFetcher(Fetcher):
    SITE = 'CodeChef'
    BASE_URL = 'https://wwww.codechef.com'
    CONTESTS_URL = 'https://www.codechef.com/contests'

    def __init__(self, refresh_interval=600):
        super().__init__(refresh_interval)

    async def run(self):
        logger.info(f'Setting up {self.SITE} fetcher...')
        await super().run()

    async def update(self):
        """Overrides update method in Fetcher"""
        html = await self.request(self.CONTESTS_URL)
        soup = BeautifulSoup(html, 'lxml')

        future_table = soup.find_all('table', class_='dataTable')[1]
        body = future_table.find('tbody')
        rows = body.find_all('tr')
        self.future_contests = []
        for row in rows:
            vals = row.find_all('td')
            url = self.BASE_URL + '/' + str(vals[0].string)
            name = str(vals[1].string)
            fmt = '%Y-%m-%dT%H:%M:%S%z'
            modify = lambda s: ''.join(s.rsplit(':', 1))
            # Actually the string format is like so: 2018-09-07T15:00:00+05:30, modify removes the last colon.
            start = datetime.strptime(modify(vals[2]['data-starttime']), fmt)
            start = int(start.timestamp())
            end = datetime.strptime(modify(vals[3]['data-endtime']), fmt)
            end = int(end.timestamp())
            length = end - start
            self.future_contests.append(Contest(name, self.SITE, url, start, length))
        self.future_contests.sort()
        logger.info(f'Updated! {len(self.future_contests)} upcoming')
        logger.debug(f'Fetched contests: {self.future_contests}')
        self.last_fetched = time.time()

    async def request(self, path):
        headers = {'User-Agent': f'aiohttp/{aiohttp.__version__}'}
        logger.debug(f'GET {path} {headers}')
        async with aiohttp.request('GET', f'{path}', headers=headers) as response:
            response.raise_for_status()
            return await response.text()
