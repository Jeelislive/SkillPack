"""
AI Tagging Pipeline using Groq (free tier)
Tags each skill with: category, sub-categories, tags,
role keywords, task keywords, quality score, platform compatibility.
"""

import json
import asyncio
from openai import AsyncOpenAI
from rich import print
from tenacity import retry, stop_after_attempt, wait_exponential
from config import get_settings

settings = get_settings()

CATEGORIES = [
    "frontend", "backend", "fullstack", "devops", "data-science",
    "ml-ai", "mobile", "security", "database", "api-design",
    "testing", "documentation", "cloud", "blockchain",
    "game-dev", "embedded", "design-systems", "productivity",
    "code-quality", "other",
]

PLATFORMS = ["claude_code", "cursor", "copilot", "continue", "universal"]

TAGGING_PROMPT = """You are an expert at categorizing AI agent skills.

Analyze the following skill and return a JSON object with these exact fields:

{{
  "primary_category": "<one of: {categories}>",
  "sub_categories": ["<2-5 specific sub-topics, e.g. css, animation, react, docker>"],
  "tags": ["<5-10 relevant tags>"],
  "role_keywords": ["<3-6 developer roles this skill helps, e.g. frontend developer, ui engineer>"],
  "task_keywords": ["<3-6 specific tasks this enables, e.g. build landing page, animate elements>"],
  "platforms": ["<compatible platforms from: {platforms}>"],
  "quality_score": <float 0-10, based on content depth, clarity, practical value>,
  "summary": "<one sentence description if none exists>"
}}

Rules:
- primary_category must be exactly one of the listed categories
- quality_score: 0-3 = stub/minimal, 4-6 = decent, 7-8 = good, 9-10 = exceptional
- If the skill content is very short (<200 chars), quality_score max is 4
- platforms: if unclear, default to ["claude_code"]
- Return ONLY valid JSON, no markdown, no explanation

Skill Name: {name}
Skill Description: {description}

Skill Content:
{content}
"""


class SkillTagger:
    def __init__(self):
        self.groq = AsyncOpenAI(
            api_key=settings.groq_api_key,
            base_url=settings.groq_base_url,
        )
        self.nvidia = AsyncOpenAI(
            api_key=settings.nvidia_api_key,
            base_url=settings.nvidia_base_url,
        ) if settings.nvidia_api_key else None

        self._request_count = 0
        self._semaphore = asyncio.Semaphore(5)  # max 5 concurrent Groq calls

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=5, max=30))
    async def _call_groq(self, prompt: str) -> str:
        self._request_count += 1
        resp = await self.groq.chat.completions.create(
            model=settings.groq_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=512,
        )
        return resp.choices[0].message.content.strip()

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=5, max=20))
    async def _call_nvidia(self, prompt: str) -> str:
        if not self.nvidia:
            raise Exception("NVIDIA not configured")
        resp = await self.nvidia.chat.completions.create(
            model=settings.nvidia_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=512,
        )
        return resp.choices[0].message.content.strip()

    async def tag_skill(self, skill: dict) -> dict:
        """Tag a single skill. Returns skill dict with AI fields populated."""
        async with self._semaphore:
            content = (skill.get("raw_content") or "")[:3000]  # cap at 3k chars for token efficiency
            name = skill.get("name", "")
            description = skill.get("description", "")

            prompt = TAGGING_PROMPT.format(
                categories=", ".join(CATEGORIES),
                platforms=", ".join(PLATFORMS),
                name=name,
                description=description,
                content=content,
            )

            raw = None
            try:
                raw = await self._call_groq(prompt)
                # Strip any markdown code fences
                raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
                result = json.loads(raw)

                # Validate and normalize
                result["primary_category"] = result.get("primary_category", "other")
                if result["primary_category"] not in CATEGORIES:
                    result["primary_category"] = "other"

                result["quality_score"] = max(0, min(10, float(result.get("quality_score", 0))))
                result["platforms"] = [p for p in result.get("platforms", ["claude_code"]) if p in PLATFORMS]
                if not result["platforms"]:
                    result["platforms"] = ["claude_code"]

                # Update description if empty
                if not skill.get("description") and result.get("summary"):
                    skill["description"] = result["summary"]

                skill.update({
                    "primary_category": result["primary_category"],
                    "sub_categories": result.get("sub_categories", [])[:5],
                    "tags": result.get("tags", [])[:10],
                    "role_keywords": result.get("role_keywords", [])[:6],
                    "task_keywords": result.get("task_keywords", [])[:6],
                    "platforms": result["platforms"],
                    "quality_score": result["quality_score"],
                })
                return skill

            except json.JSONDecodeError:
                # Try NVIDIA fallback
                if self.nvidia:
                    try:
                        raw = await self._call_nvidia(prompt)
                        raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
                        result = json.loads(raw)
                        skill["primary_category"] = result.get("primary_category", "other")
                        skill["quality_score"] = float(result.get("quality_score", 3))
                        skill["platforms"] = result.get("platforms", ["claude_code"])
                        skill["tags"] = result.get("tags", [])
                        skill["sub_categories"] = result.get("sub_categories", [])
                        skill["role_keywords"] = result.get("role_keywords", [])
                        skill["task_keywords"] = result.get("task_keywords", [])
                        return skill
                    except Exception:
                        pass

                # Final fallback: basic heuristics
                return self._heuristic_tag(skill)

            except Exception as e:
                print(f"[red]Tagging error for {skill.get('slug')}: {e}[/red]")
                return self._heuristic_tag(skill)

    def _heuristic_tag(self, skill: dict) -> dict:
        """Keyword-based tagger. No AI, no rate limits. Used for all bulk crawls."""
        text = f"{skill.get('name','')} {skill.get('description','')} {skill.get('raw_content','')}".lower()

        # Category detection via keyword map (most specific first)
        keyword_map = {
            "frontend":     ["react", "vue", "css", "html", "tailwind", "nextjs", "next.js", "svelte", "ui design", "animation", "typography", "responsive"],
            "backend":      ["api", "server", "node", "django", "fastapi", "express", "flask", "rest", "graphql endpoint", "microservice"],
            "devops":       ["docker", "kubernetes", "ci/cd", "github actions", "deploy", "terraform", "ansible", "infra", "pipeline", "helm"],
            "database":     ["sql", "postgres", "mysql", "mongodb", "redis", "database", "query", "schema", "migration", "orm"],
            "testing":      ["test", "jest", "pytest", "cypress", "playwright", "vitest", "qa", "unit test", "integration test"],
            "security":     ["auth", "oauth", "jwt", "security", "vulnerability", "pentest", "xss", "csrf", "encryption"],
            "ml-ai":        ["machine learning", "neural", "llm", "model training", "pytorch", "tensorflow", "transformers", "fine-tun", "prompt"],
            "mobile":       ["ios", "android", "react native", "flutter", "swift", "kotlin", "mobile app"],
            "cloud":        ["aws", "gcp", "azure", "cloud", "serverless", "lambda", "s3", "ec2", "cloudformation"],
            "data-science": ["pandas", "numpy", "matplotlib", "data analysis", "visualization", "jupyter", "scikit"],
            "api-design":   ["openapi", "swagger", "api design", "rest api", "graphql schema", "endpoint design"],
            "documentation":["docs", "readme", "documentation", "mkdocs", "docstring"],
            "code-quality": ["lint", "eslint", "prettier", "refactor", "clean code", "solid", "dry principle"],
            "productivity": ["workflow", "automation", "shortcut", "snippet", "template"],
        }

        primary_category = "other"
        matched_keywords = []
        for cat, keywords in keyword_map.items():
            hits = [k for k in keywords if k in text]
            if hits:
                primary_category = cat
                matched_keywords = hits
                break

        # Sub-categories: all keyword map categories that have hits
        sub_categories = []
        for cat, keywords in keyword_map.items():
            if cat != primary_category and any(k in text for k in keywords):
                sub_categories.append(cat)

        # Tags from matched keywords + name words
        name_words = skill.get("name", "").lower().replace("-", " ").replace("_", " ").split()
        tags = list(dict.fromkeys(matched_keywords[:5] + name_words[:5]))[:10]

        # Quality score based on content length (best available signal without AI)
        content_len = skill.get("content_length") or len(skill.get("raw_content") or "")
        if content_len == 0:
            quality_score = 2.0
        elif content_len < 300:
            quality_score = 3.5
        elif content_len < 1000:
            quality_score = 5.0
        elif content_len < 3000:
            quality_score = 6.5
        elif content_len < 6000:
            quality_score = 7.5
        else:
            quality_score = 8.5

        # Platform detection
        platforms = ["claude_code"]
        if ".cursorrules" in skill.get("raw_url", "") or "cursor" in text[:200]:
            platforms = ["cursor"]
        elif "copilot" in skill.get("raw_url", ""):
            platforms = ["copilot"]

        skill["primary_category"] = skill.get("primary_category") or primary_category
        skill["sub_categories"]   = skill.get("sub_categories") or sub_categories[:4]
        skill["tags"]             = skill.get("tags") or tags
        skill["role_keywords"]    = skill.get("role_keywords") or []
        skill["task_keywords"]    = skill.get("task_keywords") or []
        skill["platforms"]        = skill.get("platforms") or platforms
        skill["quality_score"]    = quality_score
        return skill

    def compute_popularity_score(self, skill: dict) -> float:
        """Normalize popularity: 0-10 based on install_count + github_stars."""
        installs = skill.get("install_count", 0)
        stars = skill.get("github_stars", 0)
        # Log scale: 100k installs = 10, 1k = 6, 100 = 4, 10 = 2
        import math
        install_score = min(10, math.log10(max(installs, 1)) * 2)
        star_score = min(10, math.log10(max(stars, 1)) * 2.5)
        return round(install_score * 0.7 + star_score * 0.3, 2)

    def tag_batch_fast(self, skills: list[dict]) -> list[dict]:
        """
        Fast heuristic tagging — no AI, no rate limits.
        Processes all skills instantly using keyword matching.
        Use this for the initial bulk crawl.
        AI tagging (tag_batch) is reserved for edge cases only.
        """
        tagged = []
        for skill in skills:
            result = self._heuristic_tag(skill)
            result["popularity_score"] = self.compute_popularity_score(result)
            tagged.append(result)
        return tagged

    async def tag_batch(self, skills: list[dict], delay_between: float = 2.0) -> list[dict]:
        """
        AI tagging via Groq — use only for skills where heuristics give low confidence.
        Groq free tier: ~30 req/min → 2s delay between requests.
        """
        tagged = []
        total = len(skills)

        for i, skill in enumerate(skills):
            if i > 0 and i % 25 == 0:
                print(f"[cyan]Progress: {i}/{total} tagged. Sleeping 10s for rate limits...[/cyan]")
                await asyncio.sleep(10)

            result = await self.tag_skill(skill)
            result["popularity_score"] = self.compute_popularity_score(result)
            tagged.append(result)

            if i % 100 == 0 and i > 0:
                print(f"[green]Tagged {i}/{total} skills[/green]")

            await asyncio.sleep(delay_between)

        return tagged
