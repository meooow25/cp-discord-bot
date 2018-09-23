import aiohttp

from .competitive_programming_site import Site, ContestFetcher
from .models import Contest


class Codeforces(Site):
    SITE_VARS = Site.SiteVars(
        name='Codeforces',
        api_url='http://codeforces.com/api',
        api_contests_path='/contest.list',
        contests_url='http://codeforces.com/contests'
    )

    def __init__(self, contest_fetcher=None, refresh_interval=600):
        if contest_fetcher is None:
            contest_fetcher = CodeforcesContestFetcher(self.SITE_VARS)
        super().__init__(contest_fetcher, refresh_interval)

    def __repr__(self):
        return self.SITE_VARS.name


class CodeforcesContestFetcher(ContestFetcher):

    def __init__(self, site_vars):
        super().__init__(site_vars)

    async def fetch(self):
        """Overrides fetch method in ContestFetcher"""
        data = await self._request(self.site_vars.api_contests_path)
        assert data['status'] == 'OK', data['comment']
        contests = [contest for contest in data['result'] if contest['phase'] == 'BEFORE']
        future_contests = [Contest(contest['name'],
                                   self.site_vars.name,
                                   f'{self.site_vars.contests_url}/{contest["id"]}',
                                   contest.get('startTimeSeconds'),
                                   contest['durationSeconds']) for contest in contests]
        # TODO: Consider how to handle contests with missing start
        future_contests = [contest for contest in future_contests if contest.start is not None]
        future_contests.sort()
        return future_contests

    async def _request(self, path, **kwargs):
        path = self.site_vars.api_url + path
        self.logger.debug(f'GET {path} {kwargs}')
        async with aiohttp.request('GET', path, params=kwargs) as response:
            response.raise_for_status()
            return await response.json()
