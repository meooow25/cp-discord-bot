from .competitive_programming_site import Site, ContestFetcher


class CompositeSite(Site):
    SITE_VARS = Site.SiteVars(name='CompositeSite')

    def __init__(self, sites, contest_fetcher=None, refresh_interval=None):
        if contest_fetcher is None:
            contest_fetcher = CompositeContestFetcher(self.SITE_VARS, sites)
        if refresh_interval is None:
            refresh_interval = min(site.refresh_interval for site in sites)
        super().__init__(contest_fetcher, refresh_interval)
        self.sites = sites

    async def run(self):
        self.logger.info('Setting up CompositeSite...')
        for site in self.sites:
            await site.run()
        await super().run()

    def __repr__(self):
        return self.SITE_VARS.name


class CompositeContestFetcher(ContestFetcher):

    def __init__(self, site_vars, sites):
        super().__init__(site_vars)
        self.sites = sites

    async def fetch(self):
        """Overrides fetch method in ContestFetcher"""
        future_contests = []
        for site in self.sites:
            future_contests += site.future_contests
        future_contests.sort()
        return future_contests
