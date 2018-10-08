from datetime import datetime

import aiohttp
from bs4 import BeautifulSoup

from .competitive_programming_site import CPSite
from .models import Contest, Profile


class AtCoder(CPSite):
    NAME = 'AtCoder'
    TAG = 'at'
    BASE_URL = 'https://beta.atcoder.jp'
    CONTESTS_PATH = '/contests'
    USERS_PATH = '/users'

    def __init__(self, contest_refresh_interval=10*60, user_refresh_interval=45*60, user_delay_interval=10):
        super().__init__(contest_refresh_interval, user_refresh_interval, user_delay_interval)

    def __repr__(self):
        return self.NAME

    async def _request(self, path):
        path = self.BASE_URL + path
        headers = {'User-Agent': f'aiohttp/{aiohttp.__version__}'}
        self.logger.debug(f'GET {path} {headers}')
        async with aiohttp.request('GET', path, headers=headers) as response:
            response.raise_for_status()
            return await response.text()

    async def fetch_future_contests(self):
        """Overrides method in Site"""
        html = await self._request(self.CONTESTS_PATH)
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
            url = self.BASE_URL + name_tag['href']
            name = str(name_tag.string)

            # The duration format is like so: 01:40
            duration_str = str(vals[2].string)
            hrs, mins = duration_str.split(':')
            length = int(hrs) * 60 * 60 + int(mins) * 60

            future_contests.append(Contest(name, self.TAG, self.NAME, url, start, length))

        future_contests.sort()
        return future_contests

    async def fetch_profile(self, handle):
        path = self.USERS_PATH + '/' + handle
        try:
            html = await self._request(path)
        except aiohttp.ClientResponseError as err:
            if err.status == 404:
                # User not found.
                return None
            raise

        soup = BeautifulSoup(html, 'html.parser')

        # No option of real name on AtCoder.
        name = None

        rating_heading = soup.find('th', text='Rating')
        if rating_heading is None:
            # User is unrated.
            rating = None
        else:
            rating_tag = rating_heading.next_sibling.span
            rating = int(rating_tag.string)
        return Profile(handle, self.TAG, self.NAME, self.BASE_URL + path, name, rating)
