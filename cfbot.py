import json
import asyncio
import aiohttp

class CFBot:

    API_URL = 'http://codeforces.com/api'


    def __init__(self, interval_sec=600):
        self.contest = None
        self.future_contests = None
        self.interval_sec = interval_sec


    def get_contests(self):
        return self.contests

    def get_future_contests(self, cnt):
        if cnt == 'all':
            return self.future_contests[:]
        return self.future_contests[:cnt]


    async def init(self):
        print('Setting up CFBot...')
        
        # inital fetch
        await self.update()

        # schedule for future
        asyncio.ensure_future(self.updater_task())


    async def update(self):
        data = await self.request('/contest.list', gym='false')
        assert data['status'] == 'OK', data['comment']
        self.contests = data['result']
        '''with open('cache.json') as file:
            self.contests = json.load(file)
            print('Loaded json')'''
        self.future_contests = [contest for contest in self.contests if contest['phase'] == 'BEFORE']
        self.future_contests.sort(key=lambda contest: contest['startTimeSeconds'])
        print(f'Updated! {len(self.contests)} total and {len(self.future_contests)} upcoming')


    async def updater_task(self):
        while True:
            await asyncio.sleep(self.interval_sec)
            await self.update()


    async def request(self, path, **kwargs):
        async with aiohttp.request('GET', f'{self.API_URL}{path}', params=kwargs) as response:
            assert response.status == 200, response.reason
            return await response.json()
