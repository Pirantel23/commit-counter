import asyncio
import aiohttp
from datetime import datetime
from commit import Commit
from repository import Repository
from collections import Counter
import coloring as cl
from exceptions import RateExceededException, EmptyRepositoryException

ENDPOINT = 'https://api.github.com'


class Client:
    def __init__(self, token: str) -> None:
        self.token = token
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={'Authorization': f'token {self.token}'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    async def make_request(self, url: str, headers: dict[str, str] = None, params: dict[str, str] = None) -> dict:
        
        async with self.session.get(url, headers=headers, params=params) as response:            
                if response.status == 200:
                    return await response.json()

                if response.status == 409:
                    raise EmptyRepositoryException

                raise Exception(f'Request failed with status code {response.status}\n{response.text}')
    
    async def get_rate_limit(self) -> dict:
        rate_limit = await self.make_request(f'{ENDPOINT}/rate_limit')

        rate = rate_limit['resources']['core']

        if rate['remaining'] == 0:
            raise RateExceededException

        return {
            'limit': rate['limit'],
            'remaining': rate['remaining'],
            'reset': datetime.fromtimestamp(rate['reset'])
        }
    
    async def get_repos(self, organisation) -> list[Repository]:
        repos = []
        page = 1

        while 1:
            params = {
                "page": page,
                "per_page": 100
            }
            print(f'{cl.YELLOW}Checking repository page {page}{cl.RESET}')

            try:
                current = ([Repository(repo['full_name']) for repo in await self.make_request(f'{ENDPOINT}/users/{organisation}/repos', params=params)])
                if not current:
                    break
                repos.extend(current)
            except Exception:
                break

            page+=1
        return repos

    async def process_repo(self, repo: Repository) -> Counter:
        print(f'{cl.CYAN}Processing {repo}{cl.RESET}')
        commits = await self.get_commits(repo)
        counter = Counter(commit for commit in commits if commit is not None)
        print(f'{cl.MAGENTA}Finished {repo}{cl.RESET}')
        return counter

    async def get_statistics(self, repos: list[Repository]) -> Counter:
        tasks = [self.process_repo(repo) for repo in repos]

        sum_counter = Counter()
        for counter in await asyncio.gather(*tasks):
            sum_counter += counter

        return sum_counter

    async def fetch_commits(self, repo, page):
        print(f'Fetching page {page} of {repo}')
        params = {
                "page": page,
                "per_page": 100
            }
        try:
            current = await self.make_request(f'{ENDPOINT}/repos/{repo.name}/commits', params=params)
        except Exception:
            return []
        return current

    async def get_commits(self, repo: Repository) -> list[Commit]:
        commits = []
        page = 1
        tasks = []
        while 1:
            tasks.append(self.fetch_commits(repo, page))
            page+=1
            if len(tasks) >= 5:
                current = await asyncio.gather(*tasks)
                if not current:
                    break
                tasks = []
                for c in current:
                    if not c:
                        break
                    commits.extend(c)
            if not tasks:
                break
        if tasks:
            current = await asyncio.gather(*tasks)
            for c in current:
                if not c:
                    break
                commits.extend(c)          

        return [c for commit in commits if (c := Commit.from_dict(commit)) is not None]