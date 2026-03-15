"""
Bundle Generator
Creates role-based and task-based skill bundles from the DB.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, cast, String
from db.models import Skill, Bundle, BundleCommand
from pipeline.install_generator import InstallGenerator
from rich import print

ROLE_BUNDLES = [
    {
        "slug": "frontend",
        "name": "Frontend Developer",
        "description": "Everything a frontend developer needs: UI, CSS, animation, React, accessibility, performance.",
        "type": "role",
        "category": "frontend",
        "role_keywords": ["frontend", "ui", "css", "react", "vue", "web"],
    },
    {
        "slug": "backend",
        "name": "Backend Developer",
        "description": "APIs, databases, auth, server architecture, and backend best practices.",
        "type": "role",
        "category": "backend",
        "role_keywords": ["backend", "api", "server", "node", "python", "rest"],
    },
    {
        "slug": "fullstack",
        "name": "Full Stack Developer",
        "description": "End-to-end skills covering frontend, backend, databases, and deployment.",
        "type": "role",
        "category": "fullstack",
        "role_keywords": ["fullstack", "full stack", "frontend", "backend", "database"],
    },
    {
        "slug": "devops",
        "name": "DevOps Engineer",
        "description": "CI/CD, Docker, Kubernetes, cloud infrastructure, monitoring, and automation.",
        "type": "role",
        "category": "devops",
        "role_keywords": ["devops", "infrastructure", "ci/cd", "docker", "kubernetes", "cloud"],
    },
    {
        "slug": "data-science",
        "name": "Data Scientist",
        "description": "Data analysis, visualization, statistical modeling, and data pipelines.",
        "type": "role",
        "category": "data-science",
        "role_keywords": ["data scientist", "data analyst", "data engineer", "analytics"],
    },
    {
        "slug": "ml-ai",
        "name": "ML / AI Engineer",
        "description": "Machine learning, LLMs, model training, prompt engineering, and AI deployment.",
        "type": "role",
        "category": "ml-ai",
        "role_keywords": ["machine learning", "ai", "llm", "deep learning", "mlops"],
    },
    {
        "slug": "security",
        "name": "Security Engineer",
        "description": "Application security, auth, vulnerability scanning, secure coding practices.",
        "type": "role",
        "category": "security",
        "role_keywords": ["security", "penetration testing", "auth", "oauth", "vulnerability"],
    },
    {
        "slug": "mobile",
        "name": "Mobile Developer",
        "description": "iOS, Android, React Native, and Flutter development skills.",
        "type": "role",
        "category": "mobile",
        "role_keywords": ["mobile", "ios", "android", "react native", "flutter"],
    },
    {
        "slug": "database",
        "name": "Database Engineer",
        "description": "SQL, NoSQL, query optimization, schema design, and data modeling.",
        "type": "role",
        "category": "database",
        "role_keywords": ["database", "dba", "sql", "postgres", "mongodb", "redis"],
    },
    {
        "slug": "testing",
        "name": "QA / Testing Engineer",
        "description": "Unit tests, integration tests, E2E testing, TDD, and quality automation.",
        "type": "role",
        "category": "testing",
        "role_keywords": ["qa", "testing", "test engineer", "quality assurance"],
    },
    {
        "slug": "cloud",
        "name": "Cloud Engineer",
        "description": "AWS, GCP, Azure, serverless, cloud-native architecture and IaC.",
        "type": "role",
        "category": "cloud",
        "role_keywords": ["cloud", "aws", "gcp", "azure", "serverless", "terraform"],
    },
    {
        "slug": "api-design",
        "name": "API Designer",
        "description": "REST, GraphQL, OpenAPI, versioning, documentation, and API best practices.",
        "type": "role",
        "category": "api-design",
        "role_keywords": ["api", "rest", "graphql", "openapi", "api design"],
    },
]

TASK_BUNDLES = [
    {
        "slug": "build-landing-page",
        "name": "Build a Landing Page",
        "description": "Skills for designing and building a high-converting landing page.",
        "type": "task",
        "category": "frontend",
        "task_keywords": ["landing page", "website", "design", "conversion"],
    },
    {
        "slug": "setup-cicd",
        "name": "Set Up CI/CD Pipeline",
        "description": "Skills for automating build, test, and deployment workflows.",
        "type": "task",
        "category": "devops",
        "task_keywords": ["ci/cd", "github actions", "deployment", "automation"],
    },
    {
        "slug": "write-unit-tests",
        "name": "Write Unit Tests",
        "description": "Skills for writing comprehensive unit and integration tests.",
        "type": "task",
        "category": "testing",
        "task_keywords": ["unit test", "testing", "jest", "pytest"],
    },
    {
        "slug": "design-rest-api",
        "name": "Design a REST API",
        "description": "Skills for designing, documenting, and building RESTful APIs.",
        "type": "task",
        "category": "api-design",
        "task_keywords": ["rest api", "api design", "openapi", "swagger"],
    },
    {
        "slug": "setup-auth",
        "name": "Implement Authentication",
        "description": "Skills for adding secure authentication and authorization.",
        "type": "task",
        "category": "security",
        "task_keywords": ["authentication", "oauth", "jwt", "auth", "login"],
    },
]


def _dedup_parent_child(skills: list[Skill]) -> list[Skill]:
    """Remove parent repo slugs (owner/repo) when a child skill (owner/repo/skillId)
    from the same repo is already in the list — prevents duplicate entries."""
    child_prefixes: set[str] = set()
    for s in skills:
        parts = s.slug.split("/")
        if len(parts) >= 3:
            child_prefixes.add(f"{parts[0]}/{parts[1]}")

    return [
        s for s in skills
        if not (len(s.slug.split("/")) == 2 and s.slug in child_prefixes)
    ]


class BundleGenerator:
    def __init__(self, db: Session):
        self.db = db
        self.install_gen = InstallGenerator()

    def _get_skills_for_bundle(
        self,
        category: str,
        role_keywords: list[str] | None = None,
        task_keywords: list[str] | None = None,
        limit: int = 30,
    ) -> list[Skill]:
        """Fetch top skills for a bundle by category + keyword matching."""
        if category == "fullstack":
            cat_filter = Skill.primary_category.in_(["frontend", "backend", "database", "fullstack"])
        else:
            cat_filter = Skill.primary_category == category

        skills = (
            self.db.query(Skill)
            .filter(
                Skill.is_active == True,
                Skill.tier == 1,
                Skill.quality_score >= 4,
                cat_filter,
            )
            .order_by(
                (Skill.quality_score * 0.6 + Skill.popularity_score * 0.4).desc()
            )
            .limit(limit * 2)
            .all()
        )

        # If still not enough, lower quality threshold but STAY within the same category
        if len(skills) < 15:
            existing_ids = {s.id for s in skills}
            lower = (
                self.db.query(Skill)
                .filter(
                    Skill.is_active == True,
                    Skill.tier == 1,
                    Skill.quality_score >= 3,
                    cat_filter,
                )
                .order_by((Skill.quality_score * 0.6 + Skill.popularity_score * 0.4).desc())
                .limit(limit)
                .all()
            )
            skills.extend([s for s in lower if s.id not in existing_ids])

        # Remove parent repo slugs (owner/repo) when a child skill (owner/repo/skillId)
        # from the same repo is already included — avoids duplicate entries
        skills = _dedup_parent_child(skills)

        return skills[:limit]

    def _upsert_bundle(self, bundle_def: dict, skill_ids: list[int]) -> Bundle:
        existing = self.db.query(Bundle).filter_by(slug=bundle_def["slug"]).first()

        if existing:
            existing.skill_ids   = skill_ids
            existing.skill_count = len(skill_ids)
            self.db.commit()
            self.db.refresh(existing)
            return existing

        bundle = Bundle(
            slug        = bundle_def["slug"],
            name        = bundle_def["name"],
            description = bundle_def["description"],
            type        = bundle_def["type"],
            category    = bundle_def.get("category", "other"),
            skill_ids   = skill_ids,
            skill_count = len(skill_ids),
            is_featured = bundle_def.get("featured", False),
            created_by  = "system",
        )
        self.db.add(bundle)
        self.db.commit()
        self.db.refresh(bundle)
        return bundle

    def _generate_commands(self, bundle: Bundle, skills: list[Skill]):
        """Generate and store install commands for all platforms."""
        # Remove old commands
        self.db.query(BundleCommand).filter_by(bundle_id=bundle.id).delete()
        self.db.commit()

        platforms = ["claude_code", "cursor", "copilot", "continue", "universal"]
        for platform in platforms:
            cmd = self.install_gen.generate(skills, platform, bundle.slug)
            bc = BundleCommand(
                bundle_id=bundle.id,
                platform=platform,
                command=cmd,
            )
            self.db.add(bc)
        self.db.commit()

    def generate_all(self):
        """Generate all role + task bundles."""
        all_defs = ROLE_BUNDLES + TASK_BUNDLES
        total = len(all_defs)
        print(f"[blue]Generating {total} bundles...[/blue]")

        for i, bundle_def in enumerate(all_defs):
            category = bundle_def.get("category", "other")
            role_kw  = bundle_def.get("role_keywords", [])
            task_kw  = bundle_def.get("task_keywords", [])

            skills = self._get_skills_for_bundle(category, role_kw, task_kw, limit=30)

            if not skills:
                print(f"[yellow]  No skills found for bundle '{bundle_def['slug']}', skipping.[/yellow]")
                continue

            skill_ids = [s.id for s in skills]
            bundle = self._upsert_bundle(bundle_def, skill_ids)
            self._generate_commands(bundle, skills)

            print(f"[green]  [{i+1}/{total}] '{bundle.slug}': {len(skills)} skills[/green]")

        print("[bold green]All bundles generated.[/bold green]")
