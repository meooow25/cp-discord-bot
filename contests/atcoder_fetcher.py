import logging
from datetime import datetime

import aiohttp
from bs4 import BeautifulSoup

from .fetcher import Fetcher
from .models import Contest

logger = logging.getLogger(__name__)


class AtCoderFetcher(Fetcher):
    SITE = 'AtCoder'
    BASE_URL = 'https://beta.atcoder.jp'
    CONTESTS_URL = 'https://beta.atcoder.jp/contests'

    def __init__(self, refresh_interval=600):
        super().__init__(refresh_interval)

    async def run(self):
        logger.info(f'Setting up {self.SITE} fetcher...')
        await super().run()

    async def update(self):
        """Overrides update method in Fetcher"""
        html = await self.request(self.CONTESTS_URL)
        # TODO: Fix bs4 not finding lxml in Python 3.7
        soup = BeautifulSoup(html, 'html.parser')

        title = soup.find(text='Upcoming Contests')
        if title is None:
            self.future_contests = []
            logger.info(f'{self.SITE}: No future contests')
            self.update_last_fetched()
            return

        # Assuming table has > 0 entries if "Upcoming Contests" title is present
        h4 = title.parent
        newline = h4.next_sibling
        div = newline.next_sibling
        tbody = div.find('tbody')
        rows = tbody.find_all('tr')
        self.future_contests = []
        for row in rows:
            vals = row.find_all('td')

            time_tag = vals[0].find('time')
            # The string format is like so: 2018-09-08 21:00:00+0900
            fmt = '%Y-%m-%d %H:%M:%S%z'
            start = str(time_tag.string)
            start = datetime.strptime(start, fmt)
            start = int(start.timestamp())

            name_tag = vals[1].find('a')
            url = self.BASE_URL + name_tag['href']
            name = str(name_tag.string)

            # The duration format is like so: 01:40
            duration_str = str(vals[2].string)
            hrs, mins = duration_str.split(':')
            length = int(hrs) * 60 * 60 + int(mins) * 60

            self.future_contests.append(Contest(name, self.SITE, url, start, length))

        self.future_contests.sort()
        logger.info(f'Updated! {len(self.future_contests)} upcoming')
        logger.debug(f'Fetched contests: {self.future_contests}')
        self.update_last_fetched()

    async def request(self, path):
        headers = {'User-Agent': f'aiohttp/{aiohttp.__version__}'}
        logger.debug(f'GET {path} {headers}')
        async with aiohttp.request('GET', f'{path}', headers=headers) as response:
            response.raise_for_status()
            return await response.text()
