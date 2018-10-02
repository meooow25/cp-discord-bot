import asyncio
import logging
import time
from datetime import datetime, timezone


class ContestSite:
    def __init__(self, contest_refresh_interval):
        self.contest_refresh_interval = contest_refresh_interval
        self.future_contests = None
        self.contests_last_fetched = None
        self.logger = logging.getLogger(self.__class__.__qualname__)

    async def run(self):
        self.logger.info('Setting up site...')
        # Initial fetch.
        await self.update_contests()
        # Schedule for future.
        asyncio.create_task(self._contest_updater_task())

    async def update_contests(self):
        self.future_contests = await self.fetch_future_contests()
        self.logger.info(f'Updated! {len(self.future_contests)} upcoming')
        self.logger.debug(f'Fetched contests: {self.future_contests}')
        self.contests_last_fetched = time.time()

    async def _contest_updater_task(self):
        while True:
            try:
                await asyncio.sleep(self.contest_refresh_interval)
                await self.update_contests()
            except asyncio.CancelledError:
                self.logger.info('Received CancelledError, stopping task')
                break
            except Exception as ex:
                self.logger.exception(f'Exception in fetching: {ex}, continuing regardless')

    async def fetch_future_contests(self):
        raise NotImplementedError('This method must be overridden')

    @staticmethod
    def filter_by_site(sites):
        if not sites:
            return lambda contest: True
        return lambda contest: contest.site in sites

    @staticmethod
    def filter_by_start_min(start_min):
        return lambda contest: start_min < contest.start

    @staticmethod
    def filter_by_start_max(start_max):
        return lambda contest: contest.start <= start_max

    def _get_future_contests(self):
        """
        Returns future contests. Because the contests are fetched every self.refresh_interval time, self.future_contests
        may contain contests which have already started. This function filters out such contests.
        """
        now = datetime.now(timezone.utc).timestamp()
        future_contests = filter(self.filter_by_start_min(now), self.future_contests)
        return future_contests

    def get_future_contests_cnt(self, cnt, sites):
        self.logger.info(f'get_future_contests_cnt: {cnt} {sites}')
        future_contests = self._get_future_contests()
        filtered_by_site = filter(self.filter_by_site(sites), future_contests)
        if cnt == 'all':
            cnt = len(self.future_contests)
        return list(filtered_by_site)[:cnt]

    def get_future_contests_before(self, start_max, sites):
        future_contests = self._get_future_contests()
        filtered_by_site = filter(self.filter_by_site(sites), future_contests)
        filtered_by_start = filter(self.filter_by_start_max(start_max), filtered_by_site)
        return list(filtered_by_start)


class CPSite(ContestSite):

    def __init__(self, contest_refresh_interval, user_refresh_interval, user_delay_interval):
        super().__init__(contest_refresh_interval)
        self.user_refresh_interval = user_refresh_interval
        self.user_delay_interval = user_delay_interval
        self.get_all_users = None
        self.on_profile_fetch = None

    async def run(self, get_all_users=None, on_profile_fetch=None):
        self.get_all_users = get_all_users
        self.on_profile_fetch = on_profile_fetch
        await super().run()
        asyncio.create_task(self._user_updater_task())

    async def update_users(self):
        if self.get_all_users is None or self.on_profile_fetch is None:
            self.logger.info('Profile handlers not registered')
            return

        for user in self.get_all_users():
            old_profile = user.get_profile_for_site(self.TAG)
            if old_profile is None:
                continue
            new_profile = await self.fetch_profile(old_profile.handle)
            self.logger.info(f'Profile with handle {old_profile.handle} fetched')
            await self.on_profile_fetch(user, old_profile, new_profile)
            await asyncio.sleep(self.user_delay_interval)

    async def _user_updater_task(self):
        while True:
            try:
                await asyncio.sleep(self.user_refresh_interval)
                await self.update_users()
            except asyncio.CancelledError:
                self.logger.info('Received CancelledError, stopping task')
                break
            except Exception as ex:
                self.logger.exception(f'Exception in fetching: {ex}, continuing regardless')

    async def fetch_profile(self, handle):
        raise NotImplementedError('This method must be overridden')
