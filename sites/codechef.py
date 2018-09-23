from datetime import datetime

import aiohttp
from bs4 import BeautifulSoup

from .competitive_programming_site import Site, ContestFetcher
from .models import Contest


class CodeChef(Site):
    SITE_VARS = Site.SiteVars(
        name='CodeChef',
        base_url='https://wwww.codechef.com',
        contests_path='/contests'
    )

    def __init__(self, contest_fetcher=None, refresh_interval=600):
        if contest_fetcher is None:
            contest_fetcher = CodeChefContestFetcher(self.SITE_VARS)
        super().__init__(contest_fetcher, refresh_interval)

    def __repr__(self):
        return self.SITE_VARS.name


class CodeChefContestFetcher(ContestFetcher):

    def __init__(self, site_vars):
        super().__init__(site_vars)

    async def fetch(self):
        """Overrides fetch method in ContestFetcher"""
        html = await self._request(self.site_vars.contests_path)
        # TODO: Fix bs4 not finding lxml in Python 3.7
        soup = BeautifulSoup(html, 'html.parser')

        title = soup.find(text='Future Contests')
        if title is None:
            self.logger.info('No future contests')
            return []

        # Assuming table has > 0 entries if "Future Contests" title is present
        h3 = title.parent
        newline = h3.next_sibling
        div = newline.next_sibling
        tbody = div.find('tbody')
        rows = tbody.find_all('tr')
        future_contests = []
        for row in rows:
            vals = row.find_all('td')
            url = self.site_vars.base_url + '/' + str(vals[0].string)
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
