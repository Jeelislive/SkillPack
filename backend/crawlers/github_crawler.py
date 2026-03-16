"""
GitHub Search API crawler
Finds SKILL.md files across all public GitHub repos
that aren't already indexed by skills.sh.
"""

import hashlib
import asyncio
import httpx
from rich import print
from tenacity import retry, stop_after_attempt, wait_exponential


SEARCH_QUERIES = [
    "filename:SKILL.md",
    "filename:skill.md path:.claude/skills",
    "topic:agent-skills",
    "topic:claude-skills",
    "topic:cursor-rules filename:.cursorrules",
    "filename:SKILL.md topic:mcp",
    "filename:SKILL.md path:.claude",
    "filename:SKILL.md language:Markdown",
    "topic:claude-code-skills",
    "topic:ai-skills",
    "filename:SKILL.md stars:>0",
    "path:.claude/skills extension:md",
]

GITHUB_API = "https://api.github.com"
GITHUB_RAW = "https://raw.githubusercontent.com"


class GitHubCrawler:
    def __init__(self, tokens: list[str]):
        self.tokens = tokens
        self._token_idx = 0

    def _next_token(self) -> str:
        token = self.tokens[self._token_idx % len(self.tokens)]
        self._token_idx += 1
        return token

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._next_token()}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))
    async def search_code(
        self,
        client: httpx.AsyncClient,
        query: str,
        page: int = 1,
    ) -> dict:
        resp = await client.get(
            f"{GITHUB_API}/search/code",
            params={"q": query, "per_page": 100, "page": page},
            headers=self._headers(),
            timeout=30,
        )

        if resp.status_code == 403:
            retry_after = int(resp.headers.get("Retry-After", 60))
            print(f"[yellow]Rate limited. Waiting {retry_after}s...[/yellow]")
            await asyncio.sleep(retry_after)
            raise Exception("Rate limited")

        if resp.status_code == 422:
            # Query validation error, skip
            return {"items": [], "total_count": 0}

        resp.raise_for_status()
        return resp.json()

    async def search_repositories(
        self,
        client: httpx.AsyncClient,
        query: str,
        page: int = 1,
    ) -> dict:
        resp = await client.get(
            f"{GITHUB_API}/search/repositories",
            params={"q": query, "per_page": 100, "page": page, "sort": "stars"},
            headers=self._headers(),
            timeout=30,
        )
        if resp.status_code in (403, 429):
            await asyncio.sleep(60)
            return {"items": [], "total_count": 0}
        resp.raise_for_status()
        return resp.json()

    async def fetch_raw_content(
        self,
        client: httpx.AsyncClient,
        owner: str,
        repo: str,
        path: str = "SKILL.md",
        branch: str = "main",
    ) -> str | None:
        for b in [branch, "master", "main"]:
            url = f"{GITHUB_RAW}/{owner}/{repo}/{b}/{path}"
            try:
                resp = await client.get(url, timeout=15)
                if resp.status_code == 200:
                    return resp.text
            except Exception:
                continue
        return None

    async def fetch_repo_meta(
        self, client: httpx.AsyncClient, slug: str
    ) -> dict:
        try:
            resp = await client.get(
                f"{GITHUB_API}/repos/{slug}",
                headers=self._headers(),
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "github_stars": data.get("stargazers_count", 0),
                    "description": data.get("description", ""),
                    "published_at": data.get("pushed_at"),
                }
        except Exception:
            pass
        return {"github_stars": 0, "description": "", "published_at": None}

    def _item_to_skill(self, item: dict, query_type: str) -> dict | None:
        try:
            repo_data = item.get("repository", {})
            full_name = repo_data.get("full_name", "")
            if not full_name or "/" not in full_name:
                return None

            owner, repo = full_name.split("/", 1)
            file_path = item.get("path", "SKILL.md")

            # Detect platform from path/content hints
            platforms = ["claude_code"]
            if ".cursorrules" in file_path or "cursor" in file_path.lower():
                platforms = ["cursor"]
            elif "copilot" in file_path.lower():
                platforms = ["copilot"]

            return {
                "owner": owner,
                "repo": repo,
                "slug": full_name,
                "name": repo.replace("-", " ").replace("_", " ").title(),
                "description": repo_data.get("description", ""),
                "install_count": 0,
                "github_stars": repo_data.get("stargazers_count", 0),
                "source": "github",
                "source_url": f"https://github.com/{full_name}",
                "raw_url": f"{GITHUB_RAW}/{full_name}/main/{file_path}",
                "file_path": file_path,
                "platforms": platforms,
            }
        except Exception:
            return None

    async def crawl_query(
        self,
        client: httpx.AsyncClient,
        query: str,
        existing_slugs: set[str],
        max_pages: int = 10,
    ) -> list[dict]:
        """Run a single search query, paginate, return new skills not in existing_slugs."""
        results = []
        for page in range(1, max_pages + 1):
            try:
                data = await self.search_code(client, query, page=page)
                items = data.get("items", [])
                if not items:
                    break

                for item in items:
                    skill = self._item_to_skill(item, query)
                    if skill and skill["slug"] not in existing_slugs:
                        existing_slugs.add(skill["slug"])
                        results.append(skill)

                total = data.get("total_count", 0)
                print(f"[cyan]  Query '{query}' page {page}/{min(max_pages, (total//100)+1)}: {len(items)} items[/cyan]")

                if len(items) < 100:
                    break

                # GitHub Search API: max 1000 results per query
                if page >= 10:
                    break

                await asyncio.sleep(2)  # GitHub Search API: 30 req/min authenticated = 2s required

            except Exception as e:
                print(f"[red]Error on query '{query}' page {page}: {e}[/red]")
                break

        return results

    async def fetch_skill_contents(
        self,
        skills: list[dict],
        existing_slugs: set[str],
    ) -> list[dict]:
        """Fetch SKILL.md content for all found skills."""
        enriched = []
        async with httpx.AsyncClient() as client:
            sem = asyncio.Semaphore(8)

            async def fetch_one(skill: dict) -> dict:
                async with sem:
                    content = await self.fetch_raw_content(
                        client, skill["owner"], skill["repo"], skill.get("file_path", "SKILL.md")
                    )
                    if content:
                        skill["raw_content"] = content
                        skill["content_hash"] = hashlib.md5(content.encode()).hexdigest()
                        skill["content_length"] = len(content)
                    else:
                        skill["raw_content"] = None
                    await asyncio.sleep(0.2)
                    return skill

            enriched = await asyncio.gather(*[fetch_one(s) for s in skills])
        return list(enriched)

    async def run(self, existing_slugs: set[str] | None = None) -> list[dict]:
        """
        Full GitHub crawl across all queries.
        existing_slugs: slugs already in DB (skip these).
        """
        if existing_slugs is None:
            existing_slugs = set()

        print("[bold blue]Starting GitHub deep crawl...[/bold blue]")
        all_skills = []

        async with httpx.AsyncClient() as client:
            for query in SEARCH_QUERIES:
                print(f"[blue]Searching: {query}[/blue]")
                skills = await self.crawl_query(client, query, existing_slugs)
                all_skills.extend(skills)
                print(f"[green]  → {len(skills)} new skills found[/green]")
                await asyncio.sleep(2)

        print(f"[cyan]Total new skills from GitHub: {len(all_skills)}[/cyan]")

        # Fetch content for all found skills
        print("[blue]Fetching skill content...[/blue]")
        enriched = await self.fetch_skill_contents(all_skills, existing_slugs)

        valid = [s for s in enriched if s.get("raw_content")]
        print(f"[bold green]GitHub crawl complete: {len(valid)} skills with content[/bold green]")
        return valid
