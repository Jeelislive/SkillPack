"""
Install Command Generator
Produces platform-specific install commands for a given set of skills.
"""

from db.models import Skill


class InstallGenerator:

    def generate(self, skills: list[Skill], platform: str, bundle_slug: str = "") -> str:
        slugs = [s.slug for s in skills if s.slug]
        if not slugs:
            return ""

        method = {
            "claude_code": self._claude_code,
            "cursor":      self._cursor,
            "copilot":     self._copilot,
            "continue":    self._continue_dev,
            "universal":   self._universal,
        }.get(platform, self._universal)

        return method(slugs, bundle_slug)

    def _claude_code(self, slugs: list[str], bundle_slug: str) -> str:
        # npx skills add supports multiple repos at once
        repos = " ".join(slugs)
        return f"npx skills add {repos}"

    def _cursor(self, slugs: list[str], bundle_slug: str) -> str:
        lines = [
            f"# SkillPack: {bundle_slug} bundle for Cursor",
            f"# Run this script to download and append all skills to .cursorrules",
            "",
            "#!/bin/bash",
            'mkdir -p .cursor',
            'echo "" >> .cursorrules',
            f'echo "# SkillPack: {bundle_slug}" >> .cursorrules',
        ]
        for slug in slugs:
            raw_url = f"https://raw.githubusercontent.com/{slug}/main/SKILL.md"
            lines.append(f'curl -s {raw_url} >> .cursorrules && echo "" >> .cursorrules')
        return "\n".join(lines)

    def _copilot(self, slugs: list[str], bundle_slug: str) -> str:
        lines = [
            f"# SkillPack: {bundle_slug} bundle for GitHub Copilot",
            "#!/bin/bash",
            'mkdir -p .github',
            f'echo "# SkillPack: {bundle_slug}" >> .github/copilot-instructions.md',
        ]
        for slug in slugs:
            raw_url = f"https://raw.githubusercontent.com/{slug}/main/SKILL.md"
            lines.append(f'curl -s {raw_url} >> .github/copilot-instructions.md && echo "" >> .github/copilot-instructions.md')
        return "\n".join(lines)

    def _continue_dev(self, slugs: list[str], bundle_slug: str) -> str:
        lines = [
            f"# SkillPack: {bundle_slug} bundle for Continue.dev",
            "#!/bin/bash",
            'mkdir -p ~/.continue/skills',
        ]
        for slug in slugs:
            owner, repo = slug.split("/", 1)
            raw_url = f"https://raw.githubusercontent.com/{slug}/main/SKILL.md"
            lines.append(f'curl -s {raw_url} > ~/.continue/skills/{owner}_{repo}.md')
        return "\n".join(lines)

    def _universal(self, slugs: list[str], bundle_slug: str) -> str:
        lines = [
            f"#!/bin/bash",
            f"# SkillPack universal installer — {bundle_slug}",
            f"# Works with Claude Code, Cursor, Copilot, Continue.dev",
            "",
            'PLATFORM="${1:-claude_code}"',
            "",
            'case "$PLATFORM" in',
            '  claude_code)',
            f'    npx skills add {" ".join(slugs)}',
            '    ;;',
            '  cursor)',
            '    mkdir -p .cursor',
            '    ' + ' && '.join([
                f'curl -s https://raw.githubusercontent.com/{s}/main/SKILL.md >> .cursorrules'
                for s in slugs[:5]  # keep it readable
            ]),
            '    ;;',
            '  *)',
            f'    npx skills add {" ".join(slugs)}',
            '    ;;',
            'esac',
            "",
            'echo "✓ SkillPack installed: {bundle_slug}"',
        ]
        return "\n".join(lines)
