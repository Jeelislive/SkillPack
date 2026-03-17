"""
Install Command Generator
Produces platform-specific install commands for a given set of skills.
"""

from db.models import Skill


def _slug_to_npx_arg(slug: str) -> str:
    """Convert a DB slug to a valid `npx skills add` argument.

    skills.sh skills use 3-part slugs (owner/repo/skillId) where the skill
    lives at .agent-skills/skillId/ inside the repo - not at skillId/ root.
    The `npx skills add` CLI requires the path to be explicit.
    """
    parts = slug.split("/")
    if len(parts) == 3:
        owner, repo, skill_id = parts
        return f"{owner}/{repo}/.agent-skills/{skill_id}"
    return slug  # 2-part owner/repo slug - works as-is


class InstallGenerator:

    def generate(self, skills: list[Skill], platform: str, bundle_slug: str = "") -> str:
        skills = [s for s in skills if s.slug]
        if not skills:
            return ""

        method = {
            "claude_code": self._claude_code,
            "cursor":      self._cursor,
            "copilot":     self._copilot,
            "continue":    self._continue_dev,
            "universal":   self._universal,
        }.get(platform, self._universal)

        return method(skills, bundle_slug)

    def _claude_code(self, skills: list[Skill], bundle_slug: str) -> str:
        args = " ".join(_slug_to_npx_arg(s.slug) for s in skills)
        return f"npx skills add {args}"

    def _cursor(self, skills: list[Skill], bundle_slug: str) -> str:
        lines = [
            f"# SkillPack: {bundle_slug} bundle for Cursor",
            f"# Run this script to download and append all skills to .cursorrules",
            "",
            "#!/bin/bash",
            'mkdir -p .cursor',
            'echo "" >> .cursorrules',
            f'echo "# SkillPack: {bundle_slug}" >> .cursorrules',
        ]
        for s in skills:
            raw_url = s.raw_url or f"https://raw.githubusercontent.com/{s.slug}/main/SKILL.md"
            lines.append(f'curl -s {raw_url} >> .cursorrules && echo "" >> .cursorrules')
        return "\n".join(lines)

    def _copilot(self, skills: list[Skill], bundle_slug: str) -> str:
        lines = [
            f"# SkillPack: {bundle_slug} bundle for GitHub Copilot",
            "#!/bin/bash",
            'mkdir -p .github',
            f'echo "# SkillPack: {bundle_slug}" >> .github/copilot-instructions.md',
        ]
        for s in skills:
            raw_url = s.raw_url or f"https://raw.githubusercontent.com/{s.slug}/main/SKILL.md"
            lines.append(f'curl -s {raw_url} >> .github/copilot-instructions.md && echo "" >> .github/copilot-instructions.md')
        return "\n".join(lines)

    def _continue_dev(self, skills: list[Skill], bundle_slug: str) -> str:
        lines = [
            f"# SkillPack: {bundle_slug} bundle for Continue.dev",
            "#!/bin/bash",
            'mkdir -p ~/.continue/skills',
        ]
        for s in skills:
            owner = s.owner or s.slug.split("/")[0]
            repo = s.repo or s.slug.split("/")[1]
            raw_url = s.raw_url or f"https://raw.githubusercontent.com/{s.slug}/main/SKILL.md"
            lines.append(f'curl -s {raw_url} > ~/.continue/skills/{owner}_{repo}.md')
        return "\n".join(lines)

    def _universal(self, skills: list[Skill], bundle_slug: str) -> str:
        npx_args = " ".join(_slug_to_npx_arg(s.slug) for s in skills)
        curl_lines = " && ".join(
            f'curl -s {s.raw_url or "https://raw.githubusercontent.com/" + s.slug + "/main/SKILL.md"} >> .cursorrules'
            for s in skills[:5]
        )
        lines = [
            f"#!/bin/bash",
            f"# SkillPack universal installer - {bundle_slug}",
            f"# Works with Claude Code, Cursor, Copilot, Continue.dev",
            "",
            'PLATFORM="${1:-claude_code}"',
            "",
            'case "$PLATFORM" in',
            '  claude_code)',
            f'    npx skills add {npx_args}',
            '    ;;',
            '  cursor)',
            '    mkdir -p .cursor',
            f'    {curl_lines}',
            '    ;;',
            '  *)',
            f'    npx skills add {npx_args}',
            '    ;;',
            'esac',
            "",
            f'echo "✓ SkillPack installed: {bundle_slug}"',
        ]
        return "\n".join(lines)
