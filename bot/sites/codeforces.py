import aiohttp

from .competitive_programming_site import CPSite
from .models import Contest, Profile


class Codeforces(CPSite):
    NAME = 'Codeforces'
    TAG = 'cf'
    API_URL = 'http://codeforces.com/api'
    API_CONTESTS_PATH = '/contest.list'
    API_USERS_PATH = '/user.info'
    BASE_URL = 'http://codeforces.com'
    CONTESTS_PATH = '/contests'
    USERS_PATH = '/profile'

    def __init__(self, contest_refresh_interval=600, user_refresh_interval=1800, user_delay_interval=5):
        super().__init__(contest_refresh_interval, user_refresh_interval, user_delay_interval)

    def __repr__(self):
        return self.NAME

    async def _request(self, path, params=None, raise_for_status=True):
        path = self.API_URL + path
        self.logger.debug(f'GET {path} {params}')
        async with aiohttp.request('GET', path, params=params) as response:
            if raise_for_status:
                response.raise_for_status()
            return await response.json()

    async def fetch_future_contests(self):
        """Overrides method in Site"""
        data = await self._request(self.API_CONTESTS_PATH)
        assert data['status'] == 'OK', data['comment']
        contests = [contest for contest in data['result'] if contest['phase'] == 'BEFORE']
        future_contests = [Contest(contest['name'],
                                   self.TAG,
                                   self.NAME,
                                   f'{self.BASE_URL}{self.CONTESTS_PATH}/{contest["id"]}',
                                   contest.get('startTimeSeconds'),
                                   contest['durationSeconds']) for contest in contests]
        # TODO: Consider how to handle contests with missing start
        future_contests = [contest for contest in future_contests if contest.start is not None]
        future_contests.sort()
        return future_contests

    async def fetch_profile(self, handle):
        """Override method in Site"""
        params = {'handles': handle}
        data = await self._request(self.API_USERS_PATH, params=params, raise_for_status=False)
        if data['status'] == 'FAILED' and 'not found' in data['comment']:
            # User not found.
            return None

        result = data['result'][0]
        fullname = ' '.join([result.get('firstName', ''), result.get('lastName', '')])
        if fullname == ' ':
            fullname = None
        rating = result.get('rating')
        url = self.BASE_URL + self.USERS_PATH + '/' + handle
        return Profile(handle, self.TAG, self.NAME, url, fullname, rating)
