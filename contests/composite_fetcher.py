
import logging

from .fetcher import Fetcher

logger = logging.getLogger(__name__)


class CompositeFetcher(Fetcher):

    def __init__(self, fetchers, refresh_interval=600):
        super().__init__(refresh_interval)
        self.fetchers = fetchers

    def get_future_contests(self, cnt, sites=None):
        logger.info(f'Composite get_future_contests: {cnt} {sites}')
        if not sites:
            return super().get_future_contests(cnt)
        if cnt == 'all':
            return [contest for contest in self.future_contests if contest.site in sites]
        return [contest for contest in self.future_contests if contest.site in sites][:cnt]

    async def run(self):
        logger.info('Setting up CompositeFetcher...')
        for fetcher in self.fetchers:
            await fetcher.run()
        await super().run()

    async def update(self):
        self.future_contests = []
        for fetcher in self.fetchers:
            self.future_contests += fetcher.get_future_contests('all')
        self.future_contests.sort()
