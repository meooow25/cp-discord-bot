from .competitive_programming_site import Site


class CompositeSite(Site):
    NAME = 'CompositeSite'

    def __init__(self, sites, refresh_interval=None):
        if refresh_interval is None:
            refresh_interval = min(site.refresh_interval for site in sites)
        super().__init__(refresh_interval)
        self.sites = sites

    def __repr__(self):
        return self.NAME

    async def run(self):
        """Override method in Site"""
        self.logger.info('Setting up CompositeSite...')
        for site in self.sites:
            await site.run()
        await super().run()

    async def fetch_future_contests(self):
        """Overrides method in Site"""
        future_contests = []
        for site in self.sites:
            future_contests += site.future_contests
        future_contests.sort()
        return future_contests

    async def fetch_profile(self, site_name, handle):
        # TODO: Switch to a dict.
        site = [site for site in self.sites if site.NAME == site_name][0]
        profile = await site.fetch_profile(handle)
        self.logger.info(f'Fetcher profile: {profile}')
        return profile
