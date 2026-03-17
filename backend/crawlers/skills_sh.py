"""
skills.sh crawler - v2
Extracts individual skills from skills.sh __next_f JSON (top 600 by all-time installs)
and supplements with the trending API (pages 0-24) to reach ~5000 ranked skills.

Each skill is an INDIVIDUAL entry: {source, skillId, name, installs}
SKILL.md path is resolved per-skill using GitHub git tree API + fuzzy matching.
"""

import difflib
import hashlib
import asyncio
import httpx
from rich import print
from tenacity import retry, stop_after_attempt, wait_exponential

BASE_URL = "https://skills.sh"
GITHUB_RAW = "https://raw.githubusercontent.com"
GITHUB_API = "https://api.github.com"
WEB_HEADERS = {"User-Agent": "SkillPack-Crawler/1.0"}


class SkillsShCrawler:
    def __init__(self, github_token: str, tier1_min_installs: int = 50):
        self.github_token = github_token
        self.tier1_min_installs = tier1_min_installs
        self.gh_headers = {
            "Authorization": f"Bearer {github_token}",
            "Accept": "application/vnd.github.v3+json",
        }
        # Cache repo trees to avoid redundant API calls (many skills share a repo)
        self._repo_tree_cache: dict[str, list[str]] = {}

    # ──────────────────────────────────────────────
    # 1. Leaderboard scraping
    # ──────────────────────────────────────────────

    def _extract_initial_skills(self, html: str) -> list[dict]:
        """
        Extract initialSkills array from skills.sh __next_f RSC data.
        Each entry: {source: 'owner/repo', skillId: 'skill-name', name: str, installs: int}
        """
        idx = html.find('\\"initialSkills\\":')
        if idx < 0:
            return []
        chunk = html[idx:]
        arr_start = chunk.index('[')
        depth = 0
        in_string = False
        escape_next = False
        for i in range(arr_start, min(arr_start + 1_000_000, len(chunk))):
            c = chunk[i]
            if escape_next:
                escape_next = False
                continue
            if c == '\\':
                escape_next = True
                continue
            if c == '"':
                in_string = not in_string
                continue
            if not in_string:
                if c == '[':
                    depth += 1
                elif c == ']':
                    depth -= 1
                    if depth == 0:
                        import json
                        raw = chunk[arr_start:i + 1].replace('\\"', '"')
                        try:
                            return json.loads(raw)
                        except Exception:
                            return []
        return []

    async def scrape_leaderboard(self, max_top: int = 1500) -> list[dict]:
        """
        Get top skills from skills.sh sorted by all-time installs.
        - First 600: from SSR page (sorted by installs)
        - More: from /api/skills/trending/{page} (200 per page)
        Deduplicates and returns top max_top sorted by installs desc.
        """
        print("[blue]  Fetching skills.sh leaderboard (SSR)...[/blue]", flush=True)
        async with httpx.AsyncClient(headers=WEB_HEADERS) as client:
            resp = await client.get(BASE_URL, timeout=30)
            resp.raise_for_status()
            ssr_skills = self._extract_initial_skills(resp.text)
        print(f"[green]  SSR: {len(ssr_skills)} skills[/green]")

        def is_github_skill(s: dict) -> bool:
            """Only keep skills hosted on GitHub (source = 'owner/repo')."""
            return "/" in s.get("source", "")

        # Merge into keyed dict (source:skillId → skill)
        skills_map: dict[str, dict] = {}
        for s in ssr_skills:
            if is_github_skill(s):
                key = f"{s['source']}:{s['skillId']}"
                skills_map[key] = s

        # Supplement with trending pages until we reach max_top
        page = 0
        async with httpx.AsyncClient(headers=WEB_HEADERS) as client:
            while len(skills_map) < max_top:
                resp = await client.get(
                    f"{BASE_URL}/api/skills/trending/{page}", timeout=15
                )
                if resp.status_code != 200:
                    break
                data = resp.json()
                batch = data.get("skills", [])
                if not batch:
                    break
                for s in batch:
                    if is_github_skill(s):
                        key = f"{s['source']}:{s['skillId']}"
                        if key not in skills_map:
                            skills_map[key] = s
                if not data.get("hasMore"):
                    break
                page += 1
                await asyncio.sleep(0.3)

        # Sort by installs desc, take top max_top
        all_skills = sorted(skills_map.values(), key=lambda x: x["installs"], reverse=True)
        top = all_skills[:max_top]
        print(f"[green]  Total unique skills: {len(all_skills)}, using top {len(top)} by installs[/green]")
        return top

    # ──────────────────────────────────────────────
    # 2. Convert raw skill entries to our schema
    # ──────────────────────────────────────────────

    def _to_skill_dict(self, raw: dict) -> dict:
        """Convert skills.sh entry to our internal skill schema."""
        source = raw["source"]  # "owner/repo"
        skill_id = raw["skillId"]
        owner, repo = source.split("/", 1)
        return {
            "owner": owner,
            "repo": repo,
            "slug": f"{source}/{skill_id}",   # unique: owner/repo/skillId
            "name": skill_id.replace("-", " ").replace("_", " ").title(),
            "description": "",
            "install_count": raw.get("installs", 0),
            "source": "skills_sh",
            "source_url": f"{BASE_URL}/{source}/{skill_id}",
            "raw_url": "",
            "_source_repo": source,
            "_skill_id": skill_id,
        }

    # ──────────────────────────────────────────────
    # 3. GitHub SKILL.md content fetching
    # ──────────────────────────────────────────────

    async def _get_repo_skill_files(
        self, client: httpx.AsyncClient, source: str
    ) -> list[str]:
        """Get all SKILL.md file paths in a repo (cached per repo)."""
        if source in self._repo_tree_cache:
            return self._repo_tree_cache[source]

        for branch in ["main", "master"]:
            try:
                resp = await client.get(
                    f"{GITHUB_API}/repos/{source}/git/trees/{branch}?recursive=1",
                    headers=self.gh_headers,
                    timeout=20,
                )
                if resp.status_code == 200:
                    tree = resp.json().get("tree", [])
                    paths = [
                        item["path"] for item in tree
                        if item["type"] == "blob"
                        and item["path"].upper().endswith("SKILL.MD")
                    ]
                    self._repo_tree_cache[source] = paths
                    return paths
            except Exception:
                continue

        self._repo_tree_cache[source] = []
        return []

    def _find_best_skill_path(self, skill_files: list[str], skill_id: str) -> str | None:
        """
        Match a skillId to the best SKILL.md file path using:
        1. Exact directory name match
        2. SkillId ends with directory name (handles 'vercel-' prefix stripping)
        3. Directory name ends with skillId
        4. Fuzzy matching (difflib)
        """
        if not skill_files:
            return None

        # Extract parent dir names
        candidates = []
        for path in skill_files:
            parts = path.split("/")
            dir_name = parts[-2] if len(parts) >= 2 else parts[0]
            candidates.append((dir_name, path))

        # 1. Exact match
        for dir_name, path in candidates:
            if dir_name == skill_id:
                return path

        # 2. SkillId ends with dir_name (e.g. 'vercel-react-best-practices' ends with 'react-best-practices')
        for dir_name, path in candidates:
            if skill_id.endswith(dir_name) or skill_id.endswith("-" + dir_name):
                return path

        # 3. Dir name ends with skillId
        for dir_name, path in candidates:
            if dir_name.endswith(skill_id) or dir_name.endswith("-" + skill_id):
                return path

        # 4. SkillId contains dir_name
        for dir_name, path in candidates:
            if dir_name and dir_name in skill_id:
                return path

        # 5. Fuzzy match
        dir_names = [d for d, _ in candidates]
        matches = difflib.get_close_matches(skill_id, dir_names, n=1, cutoff=0.5)
        if matches:
            for dir_name, path in candidates:
                if dir_name == matches[0]:
                    return path

        return None

    async def fetch_skill_content(self, client: httpx.AsyncClient, skill: dict) -> dict:
        """
        Fetch SKILL.md for a single skill.
        Uses repo tree cache + fuzzy path matching to find the right file.
        """
        source = skill["_source_repo"]
        skill_id = skill["_skill_id"]
        owner, repo = skill["owner"], skill["repo"]

        skill_files = await self._get_repo_skill_files(client, source)
        matched_path = self._find_best_skill_path(skill_files, skill_id)

        if not matched_path:
            skill["raw_content"] = None
            return skill

        for branch in ["main", "master"]:
            url = f"{GITHUB_RAW}/{source}/{branch}/{matched_path}"
            try:
                resp = await client.get(url, headers=self.gh_headers, timeout=15)
                if resp.status_code == 200:
                    content = resp.text
                    skill["raw_content"] = content
                    skill["raw_url"] = url
                    skill["content_hash"] = hashlib.md5(content.encode()).hexdigest()
                    skill["content_length"] = len(content)
                    skill = self._extract_frontmatter(skill, content)
                    return skill
            except Exception:
                continue

        skill["raw_content"] = None
        return skill

    def _extract_frontmatter(self, skill: dict, content: str) -> dict:
        """Extract name and description from YAML frontmatter if present."""
        if content.startswith("---"):
            try:
                end = content.index("---", 3)
                frontmatter = content[3:end]
                for line in frontmatter.splitlines():
                    if line.startswith("name:") and not skill.get("name"):
                        skill["name"] = line.split(":", 1)[1].strip().strip('"')
                    if line.startswith("description:") and not skill.get("description"):
                        skill["description"] = line.split(":", 1)[1].strip().strip('"')
            except ValueError:
                pass
        return skill

    # ──────────────────────────────────────────────
    # 4. Main run
    # ──────────────────────────────────────────────

    async def run(self) -> tuple[list[dict], list[dict]]:
        """
        Full crawl:
        1. Get top 1500 skills from skills.sh (sorted by installs)
        2. Split into tier1 (≥ tier1_min_installs) and tier2
        3. Fetch SKILL.md content for tier1 skills
        Returns (tier1_enriched, tier2_raw)
        """
        print("[bold blue]Starting skills.sh crawl...[/bold blue]")
        raw_skills = await self.scrape_leaderboard(max_top=5000)
        skills = [self._to_skill_dict(s) for s in raw_skills]
        print(f"[green]Found {len(skills)} skills from leaderboard[/green]")

        tier1 = [s for s in skills if s["install_count"] >= self.tier1_min_installs]
        tier2 = [s for s in skills if s["install_count"] < self.tier1_min_installs]
        print(f"[cyan]Tier 1 (DB store): {len(tier1)} | Tier 2 (index only): {len(tier2)}[/cyan]")

        # Fetch content for Tier 1 - limit concurrency to avoid GitHub rate limits
        sem = asyncio.Semaphore(5)
        async with httpx.AsyncClient() as client:
            async def fetch_one(skill):
                async with sem:
                    await asyncio.sleep(0.2)
                    return await self.fetch_skill_content(client, skill)

            tier1_enriched = list(await asyncio.gather(*[fetch_one(s) for s in tier1]))

        with_content = sum(1 for s in tier1_enriched if s.get("raw_content"))
        print(f"[bold green]skills.sh crawl complete. {with_content}/{len(tier1_enriched)} tier-1 skills have content.[/bold green]")
        return tier1_enriched, tier2
