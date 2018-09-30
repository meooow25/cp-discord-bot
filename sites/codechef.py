from datetime import datetime

import aiohttp
from bs4 import BeautifulSoup

from .competitive_programming_site import Site
from .models import Contest, Profile


class CodeChef(Site):
    NAME = 'CodeChef'
    BASE_URL = 'https://wwww.codechef.com'
    CONTESTS_PATH = '/contests'
    USERS_PATH = '/users'

    def __init__(self, refresh_interval=600):
        super().__init__(refresh_interval)

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
            future_contests.append(Contest(name, self.NAME, url, start, length))

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

        name_tag = soup.find('div', class_='user-details-container').header.h2
        name = str(name_tag.string)

        rating_tag = soup.find('div', class_='rating-number')
        rating = int(rating_tag.string)
        if rating == 0:
            # User is either unrated or truly terrible at CP, assume former.
            rating = None
        return Profile(handle, self.NAME, name, rating)
