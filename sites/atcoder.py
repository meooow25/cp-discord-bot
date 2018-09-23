from datetime import datetime

import aiohttp
from bs4 import BeautifulSoup

from .competitive_programming_site import Site, ContestFetcher
from .models import Contest


class AtCoder(Site):
    SITE_VARS = Site.SiteVars(
        name='AtCoder',
        base_url='https://beta.atcoder.jp',
        contests_path='/contests'
    )

    def __init__(self, contest_fetcher=None, refresh_interval=600):
        if contest_fetcher is None:
            contest_fetcher = AtCoderContestFetcher(self.SITE_VARS)
        super().__init__(contest_fetcher, refresh_interval)

    def __repr__(self):
        return self.SITE_VARS.name


class AtCoderContestFetcher(ContestFetcher):

    def __init__(self, site_vars):
        super().__init__(site_vars)

    async def fetch(self):
        """Overrides fetch method in ContestFetcher"""
        html = await self._request(self.site_vars.contests_path)
        # TODO: Fix bs4 not finding lxml in Python 3.7
        soup = BeautifulSoup(html, 'html.parser')

        title = soup.find(text='Upcoming Contests')
        if title is None:
            self.logger.info('No future contests')
            return []

        # Assuming table has > 0 entries if "Upcoming Contests" title is present
        h4 = title.parent
        newline = h4.next_sibling
        div = newline.next_sibling
        tbody = div.find('tbody')
        rows = tbody.find_all('tr')
        future_contests = []
        for row in rows:
            vals = row.find_all('td')

            time_tag = vals[0].find('time')
            # The string format is like so: 2018-09-08 21:00:00+0900
            fmt = '%Y-%m-%d %H:%M:%S%z'
            start = str(time_tag.string)
            start = datetime.strptime(start, fmt)
            start = int(start.timestamp())

            name_tag = vals[1].find('a')
            url = self.site_vars.base_url + name_tag['href']
            name = str(name_tag.string)

            # The duration format is like so: 01:40
            duration_str = str(vals[2].string)
            hrs, mins = duration_str.split(':')
            length = int(hrs) * 60 * 60 + int(mins) * 60

            future_contests.append(Contest(name, self.site_vars.name, url, start, length))

        future_contests.sort()
        return future_contests

    async def _request(self, path):
        path = self.site_vars.base_url + path
        headers = {'User-Agent': f'aiohttp/{aiohttp.__version__}'}
        self.logger.debug(f'GET {path} {headers}')
        async with aiohttp.request('GET', path, headers=headers) as response:
            response.raise_for_status()
            return await response.text()
