import logging

from .competitive_programming_site import ContestSite


class SiteContainer(ContestSite):

    def __init__(self, sites, contest_refresh_interval=None):
        if contest_refresh_interval is None:
            contest_refresh_interval = min(site.contest_refresh_interval for site in sites)
        super().__init__(contest_refresh_interval)
        self.sites = sites
        self._site_map = {site.TAG: site for site in self.sites}
        self.logger = logging.getLogger(self.__class__.__qualname__)

    async def run(self, get_all_users=None, on_profile_fetch=None):
        self.logger.info('Setting up CompositeSite...')
        for site in self.sites:
            await site.run(
                get_all_users=get_all_users,
                on_profile_fetch=on_profile_fetch
            )
        await super().run()

    async def fetch_future_contests(self):
        """Overrides method in ContestSite"""
        future_contests = []
        for site in self.sites:
            future_contests += site.future_contests
        future_contests.sort()
        return future_contests

    async def fetch_profile(self, handle, site_tag):
        site = self._site_map[site_tag]
        profile = await site.fetch_profile(handle)
        self.logger.info(f'Fetched profile: {profile}')
        return profile

    def get_site_name(self, site_tag):
        site = self._site_map.get(site_tag)
        return None if site is None else site.NAME
