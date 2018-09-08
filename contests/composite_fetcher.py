
import logging

from .fetcher import Fetcher

logger = logging.getLogger(__name__)


class CompositeFetcher(Fetcher):

    def __init__(self, fetchers, refresh_interval=600):
        super().__init__(refresh_interval)
        self.fetchers = fetchers

    async def run(self):
        logger.info('Setting up CompositeFetcher...')
        for fetcher in self.fetchers:
            await fetcher.run()
        await super().run()

    async def update(self):
        """Overrides update method in Fetcher"""
        self.future_contests = []
        for fetcher in self.fetchers:
            self.future_contests += fetcher.future_contests
        self.future_contests.sort()
