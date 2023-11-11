from client import Client
from time import perf_counter
from datetime import datetime
import asyncio
import coloring as cl
import matplotlib.pyplot as plt
from exceptions import RateExceededException

async def main():
    TOKEN = input('Please enter your github token: ')
    async with Client(TOKEN) as client:
        while 1:
            try:
                rate_limit = await client.get_rate_limit()
            except RateExceededException:
                print(f'{cl.RED}Rate limit exceeded{cl.RESET}\nCome back later')
                break
            remaining = rate_limit['remaining']
            reset = rate_limit['reset']
            print(f'{cl.GREEN if remaining else cl.RED}You have {remaining} requests remaining.\nThe number of requests will be updated in {reset - datetime.now()}{cl.RESET}')
            org = input('Enter the name of the organisation: ')
            t1 = perf_counter()
            repos = await client.get_repos(org)
            if not repos:
                print(f'{cl.RED}The repository is empty or does not exist{cl.RESET}')
                continue
            statistics = await client.get_statistics(repos)
            statistics = {repr(k.author):v for k,v in statistics.most_common(100)}
            print(f'{cl.GREEN}Statistics done in {perf_counter() - t1}s{cl.RESET}')
            print(f'Here is a list of top 100 most active authors\n')
            [print(f'{k}: {v}') for k, v in statistics.items()]
            names = list(statistics.keys())
            commits = list(statistics.values())
            plt.barh(names, commits)
            plt.ylabel('Authors')
            plt.xlabel('Commits')
            plt.title('Commit statistics')
            plt.show()


if __name__ == '__main__':
    asyncio.run(main())