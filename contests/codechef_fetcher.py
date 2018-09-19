import logging
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
        # TODO: Fix bs4 not finding lxml in Python 3.7
        soup = BeautifulSoup(html, 'html.parser')

        title = soup.find(text='Future Contests')
        if title is None:
            self.future_contests = []
            logger.info(f'{self.SITE}: No future contests')
            self.update_last_fetched()
            return

        # Assuming table has > 0 entries if "Future Contests" title is present
        h3 = title.parent
        newline = h3.next_sibling
        div = newline.next_sibling
        tbody = div.find('tbody')
        rows = tbody.find_all('tr')
        self.future_contests = []
        for row in rows:
            vals = row.find_all('td')
            url = self.BASE_URL + '/' + str(vals[0].string)
            name = str(vals[1].string)

            # The actual string format is like so: 2018-09-07T15:00:00+05:30
            # This function removes last colon so that strptime can parse it.
            def remove_last_colon(s):
                return ''.join(s.rsplit(':', 1))

            fmt = '%Y-%m-%dT%H:%M:%S%z'
            start = remove_last_colon(vals[2]['data-starttime'])
            start = datetime.strptime(start, fmt)
            start = int(start.timestamp())
            end = remove_last_colon(vals[3]['data-endtime'])
            end = datetime.strptime(end, fmt)
            end = int(end.timestamp())
            length = end - start
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
