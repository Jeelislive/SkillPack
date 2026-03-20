"""
Manual Bundle Curator
Replaces Groq AI with hand-curated skill selections based on actual DB content review.
Run: python3 -m pipeline.manual_bundle_curator
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.orm import Session
from db.database import SyncSessionLocal
from db.models import Skill, Bundle, BundleCommand
from pipeline.install_generator import InstallGenerator
from rich import print


# ── Manually curated bundle → skill IDs mapping ──────────────────────────────
# These IDs were verified by directly reviewing skill names/descriptions in DB.
# Ordered by relevance (best first).

CURATED_BUNDLES: dict[str, list[int]] = {

    # ── Role: Frontend ─────────────────────────────────────────────────────────
    "frontend": [
        2,    # vercel-react-best-practices
        3,    # frontend-design
        14,   # next-best-practices
        17,   # tailwind-design-system
        557,  # React Doctor
        996,  # React State Management
        604,  # Design System Patterns
        957,  # Accessibility
        212,  # Web Accessibility
        609,  # Accessibility Compliance
        596,  # Javascript Testing Patterns
        554,  # E2E Testing Patterns
    ],

    "react-developer": [
        2,    # vercel-react-best-practices
        557,  # React Doctor
        996,  # React State Management
        2922, # React Critic
        309,  # Nextjs App Router Patterns
        173,  # Typescript Advanced Types
        596,  # Javascript Testing Patterns
        349,  # Javascript Typescript Jest
        554,  # E2E Testing Patterns
        17,   # tailwind-design-system
        1505, # Oxc React Compiler
        604,  # Design System Patterns
    ],

    "nextjs-developer": [
        14,   # next-best-practices
        2,    # vercel-react-best-practices
        309,  # Nextjs App Router Patterns
        940,  # Clerk Nextjs Patterns
        286,  # Next Cache Components
        557,  # React Doctor
        996,  # React State Management
        173,  # Typescript Advanced Types
        245,  # Authentication Setup
        312,  # Neon Postgres
    ],

    "vue-developer": [
        550,  # Pinia
        561,  # Nuxt
        173,  # Typescript Advanced Types
        596,  # Javascript Testing Patterns
        604,  # Design System Patterns
    ],

    "react-native-developer": [
        607,  # React Native Architecture
        346,  # React Native Best Practices
        618,  # React Native Design
        1850, # React Native Navigation
        596,  # Javascript Testing Patterns
    ],

    "flutter-developer": [
        593,  # Flutter Expert
        800,  # Flutter Architecting Apps
        799,  # Flutter Building Layouts
        804,  # Flutter Animating Apps
        304,  # Flutter Animations
        814,  # Flutter Caching Data
        822,  # Flutter Handling Concurrency
        834,  # Flutter Building Plugins
        826,  # Flutter Building Forms
        823,  # Flutter Improving Accessibility
    ],

    "ios-developer": [
        1889, # Piece Ios
        2159, # Bootstrappkit (Swift)
    ],

    # ── Role: Backend ──────────────────────────────────────────────────────────
    "backend": [
        296,  # Nodejs Backend Patterns
        542,  # Fastapi Templates
        569,  # Async Python Patterns
        991,  # Auth Implementation Patterns
        213,  # Database Schema Design
        217,  # Backend Testing
        220,  # Api Design
        282,  # Api Design Principles
        234,  # Monitoring Observability
        584,  # Github Actions Templates
    ],

    "python-developer": [
        569,  # Async Python Patterns
        542,  # Fastapi Templates
        612,  # Python Design Patterns
        958,  # Python Code Style
        976,  # Python Error Handling
        396,  # Pytest Coverage
        217,  # Backend Testing
        382,  # Python Mcp Server Generator
        991,  # Auth Implementation Patterns
    ],

    "nodejs-developer": [
        296,  # Nodejs Backend Patterns
        261,  # Npm Git Install
        546,  # Pnpm
        991,  # Auth Implementation Patterns
        596,  # Javascript Testing Patterns
        349,  # Javascript Typescript Jest
        217,  # Backend Testing
        173,  # Typescript Advanced Types
        584,  # Github Actions Templates
    ],

    "golang-developer": [
        999,  # Golang Patterns
        572,  # Golang Pro
        217,  # Backend Testing
        220,  # Api Design
        282,  # Api Design Principles
    ],

    "rust-developer": [
        643,  # Rust Async Patterns
        920,  # Rust Best Practices
        2203, # Rust Skills
        1139, # Connectrpc Axum
        437,  # Rust Mcp Server Generator
        217,  # Backend Testing
    ],

    "java-developer": [],  # insufficient Java-specific skills in DB

    "dotnet-developer": [
        491,  # Containerize Aspnetcore
        529,  # Containerize Aspnet Framework
        453,  # Aspnet Minimal Api Openapi
    ],

    "php-developer": [],  # insufficient PHP-specific skills in DB

    # ── Role: Full Stack ────────────────────────────────────────────────────────
    "fullstack": [
        2,    # vercel-react-best-practices
        14,   # next-best-practices
        296,  # Nodejs Backend Patterns
        542,  # Fastapi Templates
        213,  # Database Schema Design
        104,  # Supabase Postgres Best Practices
        931,  # Drizzle Orm
        991,  # Auth Implementation Patterns
        584,  # Github Actions Templates
        559,  # Docker Expert
        596,  # Javascript Testing Patterns
        173,  # Typescript Advanced Types
    ],

    # ── Role: DevOps / Cloud ────────────────────────────────────────────────────
    "devops": [
        559,  # Docker Expert
        338,  # Multi Stage Dockerfile
        1108, # Docker Compose Generator
        584,  # Github Actions Templates
        401,  # Create Github Action Workflow Specification
        630,  # Git Advanced Workflows
        234,  # Monitoring Observability
        581,  # Import Infrastructure As Code
        402,  # Terraform Azurerm Set Diff Analyzer
    ],

    "cloud": [
        559,  # Docker Expert
        584,  # Github Actions Templates
        581,  # Import Infrastructure As Code
        234,  # Monitoring Observability
    ],

    "aws-developer": [],  # insufficient AWS-specific skills in DB

    "platform-engineer": [
        581,  # Import Infrastructure As Code
        402,  # Terraform Azurerm Set Diff Analyzer
        584,  # Github Actions Templates
        234,  # Monitoring Observability
    ],

    "sre": [
        234,  # Monitoring Observability
        539,  # Llm Monitoring Dashboard
        2591, # Logging Architecture
        584,  # Github Actions Templates
    ],

    # ── Role: Data / ML ─────────────────────────────────────────────────────────
    "ml-ai": [
        211,  # Ai Sdk
        624,  # Langchain Architecture
        948,  # Langchain Fundamentals
        956,  # Langchain Rag
        641,  # Rag Implementation
        997,  # Langchain Middleware
        2251, # Openai Agents Python
        391,  # Ai Prompt Engineering Safety Review
        539,  # Llm Monitoring Dashboard
        445,  # Create Llms (llms.txt)
    ],

    "llm-engineer": [
        624,  # Langchain Architecture
        948,  # Langchain Fundamentals
        956,  # Langchain Rag
        641,  # Rag Implementation
        997,  # Langchain Middleware
        1001, # Langchain Dependencies
        211,  # Ai Sdk
        2251, # Openai Agents Python
        1997, # Rag Chat Project
        539,  # Llm Monitoring Dashboard
        391,  # Ai Prompt Engineering Safety Review
    ],

    "prompt-engineer": [
        391,  # Ai Prompt Engineering Safety Review
        445,  # Create Llms
        211,  # Ai Sdk
        948,  # Langchain Fundamentals (prompt patterns)
    ],

    # ── Role: Security ───────────────────────────────────────────────────────────
    "security": [
        192,  # Security Best Practices
        914,  # Security Review
        587,  # Security Requirement Extraction
        2514, # Security Analyzer
        855,  # Better Auth Security Best Practices
        991,  # Auth Implementation Patterns
        245,  # Authentication Setup
        1918, # Claude Pentest Agent Ecosystem
    ],

    "devsecops": [
        192,  # Security Best Practices
        914,  # Security Review
        584,  # Github Actions Templates
        2514, # Security Analyzer
        587,  # Security Requirement Extraction
    ],

    # ── Role: Database ───────────────────────────────────────────────────────────
    "database": [
        371,  # Postgresql Code Review
        337,  # Postgresql Optimization
        534,  # Postgresql Table Design
        104,  # Supabase Postgres Best Practices
        312,  # Neon Postgres
        931,  # Drizzle Orm
        984,  # Prisma Client Api
        998,  # Prisma Database Setup
        213,  # Database Schema Design
    ],

    "postgres-developer": [
        371,  # Postgresql Code Review
        337,  # Postgresql Optimization
        534,  # Postgresql Table Design
        104,  # Supabase Postgres Best Practices
        312,  # Neon Postgres
        213,  # Database Schema Design
    ],

    # ── Role: Testing ─────────────────────────────────────────────────────────────
    "testing": [
        596,  # Javascript Testing Patterns
        349,  # Javascript Typescript Jest
        217,  # Backend Testing
        554,  # E2E Testing Patterns
        532,  # Playwright Cli
        330,  # Playwright Generate Test
        358,  # Playwright Automation Fill In Form
        340,  # Playwright Explore Website
        396,  # Pytest Coverage
    ],

    # ── Role: API Design ──────────────────────────────────────────────────────────
    "api-design": [
        220,  # Api Design
        282,  # Api Design Principles
        216,  # Api Documentation
        463,  # Openapi To Application Code
        453,  # Aspnet Minimal Api Openapi
        282,  # Api Design Principles (Restful)
    ],

    # ── Role: Other ───────────────────────────────────────────────────────────────
    "dx-engineer": [
        261,  # Npm Git Install
        546,  # Pnpm
        630,  # Git Advanced Workflows
        227,  # Git Workflow
        208,  # Workflow Automation
        382,  # Python Mcp Server Generator
        409,  # Typescript Mcp Server Generator
    ],

    "technical-writer": [
        216,  # Api Documentation
        445,  # Create Llms (llms.txt)
        168,  # Design Md
        239,  # Changelog Maintenance
    ],

    "blockchain-developer": [
        970,  # Solidity Security
        1137, # Awesome Web3 Security
    ],

    # ── Task Bundles ──────────────────────────────────────────────────────────────
    "setup-auth": [
        991,  # Auth Implementation Patterns
        245,  # Authentication Setup
        131,  # Better Auth Best Practices
        855,  # Better Auth Security Best Practices
        954,  # Clerk
        994,  # Clerk Setup
        940,  # Clerk Nextjs Patterns
        300,  # Create Auth Skill
    ],

    "add-payments": [
        602,  # Stripe Integration
    ],

    "setup-docker": [
        559,  # Docker Expert
        1108, # Docker Compose Generator
        338,  # Multi Stage Dockerfile
        491,  # Containerize Aspnetcore
        529,  # Containerize Aspnet Framework
    ],

    "setup-cicd": [
        584,  # Github Actions Templates
        401,  # Create Github Action Workflow Specification
        630,  # Git Advanced Workflows
        227,  # Git Workflow
        208,  # Workflow Automation
    ],

    "write-unit-tests": [
        596,  # Javascript Testing Patterns
        349,  # Javascript Typescript Jest
        217,  # Backend Testing
        396,  # Pytest Coverage
        554,  # E2E Testing Patterns
        330,  # Playwright Generate Test
    ],

    "design-rest-api": [
        220,  # Api Design
        282,  # Api Design Principles
        216,  # Api Documentation
        463,  # Openapi To Application Code
        453,  # Aspnet Minimal Api Openapi
    ],

    "setup-database": [
        213,  # Database Schema Design
        104,  # Supabase Postgres Best Practices
        931,  # Drizzle Orm
        984,  # Prisma Client Api
        998,  # Prisma Database Setup
        371,  # Postgresql Code Review
        337,  # Postgresql Optimization
        534,  # Postgresql Table Design
        312,  # Neon Postgres
    ],

    "setup-monitoring": [
        234,  # Monitoring Observability
        539,  # Llm Monitoring Dashboard
        2591, # Logging Architecture
    ],

    "build-chatbot": [
        211,  # Ai Sdk
        624,  # Langchain Architecture
        956,  # Langchain Rag
        948,  # Langchain Fundamentals
        997,  # Langchain Middleware
        2251, # Openai Agents Python
    ],

    "build-saas": [
        14,   # next-best-practices
        2,    # vercel-react-best-practices
        991,  # Auth Implementation Patterns
        602,  # Stripe Integration
        104,  # Supabase Postgres Best Practices
        931,  # Drizzle Orm
        584,  # Github Actions Templates
        559,  # Docker Expert
        234,  # Monitoring Observability
    ],

    "migrate-to-typescript": [
        173,  # Typescript Advanced Types
        596,  # Javascript Testing Patterns
        409,  # Typescript Mcp Server Generator
        931,  # Drizzle Orm (type-safe ORM)
    ],

    "setup-search": [
        213,  # Database Schema Design (FTS via Postgres)
        337,  # Postgresql Optimization (FTS indices)
        641,  # Rag Implementation (semantic search)
    ],

    "add-rate-limiting": [
        192,  # Security Best Practices
        914,  # Security Review
        991,  # Auth Implementation Patterns
    ],

    "build-realtime": [
        208,  # Workflow Automation
        296,  # Nodejs Backend Patterns
    ],

    "setup-caching": [
        286,  # Next Cache Components
        337,  # Postgresql Optimization (query cache)
        213,  # Database Schema Design
    ],

    "build-landing-page": [
        3,    # frontend-design
        17,   # tailwind-design-system
        957,  # Accessibility
        212,  # Web Accessibility
        604,  # Design System Patterns
    ],

    "build-dashboard": [
        2,    # vercel-react-best-practices
        996,  # React State Management
        14,   # next-best-practices
        309,  # Nextjs App Router Patterns
    ],

    "setup-file-storage": [],

    "deploy-to-cloud": [
        584,  # Github Actions Templates
        559,  # Docker Expert
        338,  # Multi Stage Dockerfile
        581,  # Import Infrastructure As Code
    ],

    "build-cli-tool": [
        382,  # Python Mcp Server Generator
        409,  # Typescript Mcp Server Generator
        227,  # Git Workflow
        208,  # Workflow Automation
    ],

    "build-graphql-api": [
        220,  # Api Design
        282,  # Api Design Principles
        463,  # Openapi To Application Code
    ],

    "setup-notifications": [
        296,  # Nodejs Backend Patterns
        602,  # Stripe Integration (email receipts)
    ],

    "optimize-performance": [
        2,    # vercel-react-best-practices
        14,   # next-best-practices
        286,  # Next Cache Components
        337,  # Postgresql Optimization
    ],
}


def run(dry_run: bool = False):
    install_gen = InstallGenerator()
    db: Session = SyncSessionLocal()

    try:
        # Validate all skill IDs exist
        all_ids = set(sid for ids in CURATED_BUNDLES.values() for sid in ids)
        existing = {row[0] for row in db.query(Skill.id).filter(Skill.id.in_(all_ids)).all()}
        missing = all_ids - existing
        if missing:
            print(f"[yellow]Warning: {len(missing)} skill IDs not found in DB: {sorted(missing)[:20]}[/yellow]")

        updated, skipped = 0, 0
        for bundle_slug, skill_ids in CURATED_BUNDLES.items():
            # Filter to only valid IDs and deduplicate preserving order
            seen: set[int] = set()
            valid_ids = []
            for sid in skill_ids:
                if sid in existing and sid not in seen:
                    valid_ids.append(sid)
                    seen.add(sid)

            if not valid_ids:
                print(f"[yellow]  {bundle_slug}: no valid skills, skipping[/yellow]")
                skipped += 1
                continue

            bundle = db.query(Bundle).filter_by(slug=bundle_slug).first()
            if not bundle:
                print(f"[yellow]  {bundle_slug}: bundle not in DB, skipping[/yellow]")
                skipped += 1
                continue

            if dry_run:
                skills = db.query(Skill).filter(Skill.id.in_(valid_ids)).all()
                names = [s.name for s in skills]
                print(f"  [DRY] {bundle_slug}: {len(valid_ids)} skills → {names}")
                continue

            # Update skill_ids
            bundle.skill_ids = valid_ids
            bundle.skill_count = len(valid_ids)
            db.commit()

            # Regenerate install commands
            skills = db.query(Skill).filter(Skill.id.in_(valid_ids)).all()
            skill_map = {s.id: s for s in skills}
            ordered_skills = [skill_map[sid] for sid in valid_ids if sid in skill_map]

            db.query(BundleCommand).filter_by(bundle_id=bundle.id).delete()
            db.commit()
            for platform in ["claude_code", "cursor", "copilot", "continue", "universal"]:
                cmd = install_gen.generate(ordered_skills, platform, bundle_slug)
                db.add(BundleCommand(bundle_id=bundle.id, platform=platform, command=cmd))
            db.commit()

            print(f"[green]  ✓ {bundle_slug}: {len(valid_ids)} skills[/green]")
            updated += 1

        print(f"\n[bold green]Done: {updated} bundles updated, {skipped} skipped.[/bold green]")

    finally:
        db.close()


if __name__ == "__main__":
    dry = "--dry" in sys.argv
    if dry:
        print("[blue]DRY RUN - no DB changes[/blue]")
    run(dry_run=dry)
