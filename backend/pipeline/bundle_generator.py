"""
Bundle Generator
Creates role-based and task-based skill bundles from the DB.
Supports 50+ bundles with keyword-driven skill matching.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from db.models import Skill, Bundle, BundleCommand
from pipeline.install_generator import InstallGenerator
from rich import print

# ── Role Bundles ──────────────────────────────────────────────────────────────

ROLE_BUNDLES = [
    # ── Core Web ──
    {
        "slug": "frontend",
        "name": "Frontend Developer",
        "description": "UI, CSS, animations, accessibility, React, Vue, performance — everything frontend.",
        "type": "role", "category": "frontend",
        "role_keywords": ["frontend", "ui", "css", "html", "dom", "web", "react", "vue", "angular", "svelte",
                          "tailwind", "sass", "animation", "framer", "accessibility", "a11y", "responsive",
                          "webpack", "vite", "component", "design-system", "layout", "typography"],
    },
    {
        "slug": "backend",
        "name": "Backend Developer",
        "description": "APIs, databases, auth, server architecture, and backend best practices.",
        "type": "role", "category": "backend",
        "role_keywords": ["backend", "api", "server", "node", "python", "rest", "express", "fastapi", "django",
                          "flask", "middleware", "routing", "validation", "orm", "pagination", "rate-limit",
                          "websocket", "queue", "worker", "caching"],
    },
    {
        "slug": "fullstack",
        "name": "Full Stack Developer",
        "description": "End-to-end skills covering frontend, backend, databases, and deployment.",
        "type": "role", "category": "fullstack",
        "role_keywords": ["fullstack", "full-stack", "frontend", "backend", "database", "deployment",
                          "monorepo", "trpc", "next", "remix", "sveltekit", "nuxt"],
    },
    # ── Framework Specialists ──
    {
        "slug": "react-developer",
        "name": "React Developer",
        "description": "Deep React skills: hooks, state management, performance, testing, and ecosystem.",
        "type": "role", "category": "frontend",
        "role_keywords": ["react", "hooks", "jsx", "redux", "zustand", "recoil", "jotai", "react-query",
                          "tanstack", "context", "suspense", "concurrent", "fiber", "react-router",
                          "react-testing-library", "storybook", "recharts", "react-native"],
    },
    {
        "slug": "nextjs-developer",
        "name": "Next.js Developer",
        "description": "Next.js App Router, RSC, SSR, ISR, Vercel deployment, and full-stack patterns.",
        "type": "role", "category": "frontend",
        "role_keywords": ["next", "nextjs", "app-router", "rsc", "server-component", "ssr", "isr", "ssg",
                          "vercel", "edge", "middleware", "metadata", "image-optimization", "turbopack"],
    },
    {
        "slug": "vue-developer",
        "name": "Vue.js Developer",
        "description": "Vue 3, Composition API, Pinia, Nuxt, and Vue ecosystem best practices.",
        "type": "role", "category": "frontend",
        "role_keywords": ["vue", "vuejs", "composition-api", "pinia", "vuex", "nuxt", "vite", "vue-router",
                          "options-api", "reactivity", "definecomponent", "sfc", "teleport"],
    },
    {
        "slug": "angular-developer",
        "name": "Angular Developer",
        "description": "Angular, TypeScript, RxJS, NgRx, standalone components, and enterprise patterns.",
        "type": "role", "category": "frontend",
        "role_keywords": ["angular", "rxjs", "ngrx", "typescript", "injectable", "directive", "pipe",
                          "module", "standalone", "signals", "zone", "changedetection", "angular-material"],
    },
    # ── Backend Languages ──
    {
        "slug": "nodejs-developer",
        "name": "Node.js Developer",
        "description": "Node.js, Express, Fastify, async patterns, streams, and npm ecosystem.",
        "type": "role", "category": "backend",
        "role_keywords": ["nodejs", "node.js", "express", "fastify", "koa", "hapi", "npm", "yarn", "pnpm",
                          "stream", "buffer", "event-loop", "worker-thread", "cluster", "libuv"],
    },
    {
        "slug": "python-developer",
        "name": "Python Developer",
        "description": "Python, FastAPI, Django, async, data processing, and Pythonic patterns.",
        "type": "role", "category": "backend",
        "role_keywords": ["python", "fastapi", "django", "flask", "pydantic", "sqlalchemy", "alembic",
                          "asyncio", "celery", "pytest", "pip", "poetry", "pyenv", "type-hints", "dataclass"],
    },
    {
        "slug": "golang-developer",
        "name": "Go Developer",
        "description": "Go language patterns, goroutines, channels, standard library, and Go services.",
        "type": "role", "category": "backend",
        "role_keywords": ["golang", "go", "goroutine", "channel", "interface", "struct", "gin", "fiber",
                          "chi", "echo", "grpc", "protobuf", "gorm", "go-modules", "stdlib"],
    },
    {
        "slug": "rust-developer",
        "name": "Rust Developer",
        "description": "Rust ownership, async, Tokio, Actix, WebAssembly, and systems programming.",
        "type": "role", "category": "backend",
        "role_keywords": ["rust", "ownership", "borrow", "lifetime", "tokio", "actix", "axum", "serde",
                          "cargo", "trait", "enum", "wasm", "webassembly", "diesel", "sqlx"],
    },
    {
        "slug": "java-developer",
        "name": "Java Developer",
        "description": "Spring Boot, JPA, Maven/Gradle, microservices, and Java enterprise patterns.",
        "type": "role", "category": "backend",
        "role_keywords": ["java", "spring", "springboot", "hibernate", "jpa", "maven", "gradle",
                          "microservice", "kafka", "junit", "lombok", "jakarta", "servlet", "quarkus"],
    },
    {
        "slug": "dotnet-developer",
        "name": ".NET / C# Developer",
        "description": "C#, ASP.NET Core, Entity Framework, Blazor, and .NET ecosystem.",
        "type": "role", "category": "backend",
        "role_keywords": ["dotnet", "csharp", "c#", "asp.net", "aspnet", "entity-framework", "blazor",
                          "nuget", "linq", "wpf", "maui", "minimal-api", "mediatr", "dapper"],
    },
    {
        "slug": "php-developer",
        "name": "PHP Developer",
        "description": "PHP, Laravel, Symfony, Composer, and modern PHP development patterns.",
        "type": "role", "category": "backend",
        "role_keywords": ["php", "laravel", "symfony", "composer", "eloquent", "blade", "artisan",
                          "wordpress", "drupal", "phpunit", "pest", "inertia", "livewire"],
    },
    # ── Infrastructure & Ops ──
    {
        "slug": "devops",
        "name": "DevOps Engineer",
        "description": "CI/CD, Docker, Kubernetes, cloud infrastructure, monitoring, and automation.",
        "type": "role", "category": "devops",
        "role_keywords": ["devops", "infrastructure", "ci-cd", "cicd", "docker", "kubernetes", "k8s",
                          "helm", "terraform", "ansible", "jenkins", "gitlab", "github-actions",
                          "monitoring", "prometheus", "grafana", "pipeline", "automation"],
    },
    {
        "slug": "platform-engineer",
        "name": "Platform Engineer",
        "description": "Internal developer platforms, IDP, golden paths, and infrastructure abstraction.",
        "type": "role", "category": "devops",
        "role_keywords": ["platform", "idp", "backstage", "crossplane", "gitops", "argocd", "flux",
                          "operator", "custom-resource", "crd", "developer-experience", "golden-path"],
    },
    {
        "slug": "sre",
        "name": "Site Reliability Engineer",
        "description": "SLOs, SLIs, incident response, chaos engineering, and reliability practices.",
        "type": "role", "category": "devops",
        "role_keywords": ["sre", "reliability", "slo", "sli", "error-budget", "incident", "postmortem",
                          "chaos", "resilience", "alerting", "on-call", "runbook", "observability"],
    },
    {
        "slug": "cloud",
        "name": "Cloud Engineer",
        "description": "AWS, GCP, Azure, serverless, cloud-native architecture and IaC.",
        "type": "role", "category": "cloud",
        "role_keywords": ["cloud", "aws", "gcp", "azure", "serverless", "terraform", "iac", "lambda",
                          "s3", "ec2", "gke", "aks", "eks", "cloudformation", "pulumi", "cdk"],
    },
    {
        "slug": "aws-developer",
        "name": "AWS Developer",
        "description": "AWS Lambda, S3, DynamoDB, CloudFormation, CDK, and the AWS ecosystem.",
        "type": "role", "category": "cloud",
        "role_keywords": ["aws", "lambda", "s3", "dynamodb", "cloudformation", "cdk", "sam", "apigw",
                          "ecs", "fargate", "sqs", "sns", "cognito", "amplify", "cloudwatch"],
    },
    # ── Data & AI ──
    {
        "slug": "data-science",
        "name": "Data Scientist",
        "description": "Data analysis, visualization, statistical modeling, and data pipelines.",
        "type": "role", "category": "data-science",
        "role_keywords": ["data-science", "data-scientist", "pandas", "numpy", "scipy", "matplotlib",
                          "seaborn", "plotly", "statistics", "hypothesis", "regression", "classification",
                          "clustering", "jupyter", "notebook", "eda", "visualization"],
    },
    {
        "slug": "data-engineer",
        "name": "Data Engineer",
        "description": "ETL/ELT pipelines, data warehouses, Spark, dbt, Airflow, and streaming.",
        "type": "role", "category": "data-science",
        "role_keywords": ["data-engineer", "etl", "elt", "pipeline", "airflow", "spark", "kafka",
                          "flink", "dbt", "snowflake", "bigquery", "redshift", "databricks", "dask",
                          "parquet", "delta-lake", "iceberg", "warehouse"],
    },
    {
        "slug": "analytics-engineer",
        "name": "Analytics Engineer",
        "description": "dbt, SQL analytics, BI tools, metrics layers, and data modeling for analysts.",
        "type": "role", "category": "data-science",
        "role_keywords": ["analytics", "dbt", "sql", "bi", "tableau", "looker", "metabase", "superset",
                          "metrics", "dimensional-modeling", "star-schema", "olap", "cube"],
    },
    {
        "slug": "ml-ai",
        "name": "ML / AI Engineer",
        "description": "Machine learning, LLMs, model training, MLOps, and AI deployment.",
        "type": "role", "category": "ml-ai",
        "role_keywords": ["machine-learning", "ai", "llm", "deep-learning", "mlops", "pytorch", "tensorflow",
                          "keras", "sklearn", "xgboost", "lightgbm", "model", "training", "inference",
                          "embedding", "vector", "rag", "fine-tuning", "huggingface"],
    },
    {
        "slug": "llm-engineer",
        "name": "LLM Application Engineer",
        "description": "Build LLM-powered apps: RAG, agents, chains, evals, and prompt pipelines.",
        "type": "role", "category": "ml-ai",
        "role_keywords": ["llm", "langchain", "llamaindex", "openai", "anthropic", "claude", "gpt",
                          "rag", "agent", "tool-use", "function-calling", "prompt", "vector-store",
                          "chromadb", "pinecone", "weaviate", "semantic-search", "embeddings"],
    },
    {
        "slug": "prompt-engineer",
        "name": "Prompt Engineer",
        "description": "Prompt design, chain-of-thought, few-shot learning, and LLM optimization.",
        "type": "role", "category": "ml-ai",
        "role_keywords": ["prompt", "prompt-engineering", "chain-of-thought", "cot", "few-shot", "zero-shot",
                          "system-prompt", "instruction-tuning", "temperature", "sampling", "token",
                          "context-window", "jailbreak", "alignment"],
    },
    # ── Security ──
    {
        "slug": "security",
        "name": "Security Engineer",
        "description": "Application security, auth, vulnerability scanning, and secure coding.",
        "type": "role", "category": "security",
        "role_keywords": ["security", "appsec", "owasp", "penetration", "pentest", "auth", "oauth",
                          "vulnerability", "sast", "dast", "cve", "exploit", "xss", "sql-injection",
                          "csrf", "encryption", "tls", "zero-trust", "soc2", "compliance"],
    },
    {
        "slug": "devsecops",
        "name": "DevSecOps Engineer",
        "description": "Security in CI/CD, secret scanning, SAST/DAST, supply chain security.",
        "type": "role", "category": "security",
        "role_keywords": ["devsecops", "security", "sast", "dast", "secret-scanning", "trivy", "snyk",
                          "sonarqube", "sbom", "supply-chain", "signing", "cosign", "policy", "opa"],
    },
    # ── Mobile ──
    {
        "slug": "mobile",
        "name": "Mobile Developer",
        "description": "iOS, Android, React Native, and Flutter development skills.",
        "type": "role", "category": "mobile",
        "role_keywords": ["mobile", "ios", "android", "react-native", "flutter", "swift", "kotlin",
                          "objective-c", "xcode", "gradle", "app-store", "play-store", "push-notification"],
    },
    {
        "slug": "react-native-developer",
        "name": "React Native Developer",
        "description": "Cross-platform mobile with React Native, Expo, and native modules.",
        "type": "role", "category": "mobile",
        "role_keywords": ["react-native", "expo", "native-module", "metro", "hermes", "ios", "android",
                          "navigation", "react-navigation", "detox", "flipper", "eas", "bare-workflow"],
    },
    {
        "slug": "flutter-developer",
        "name": "Flutter Developer",
        "description": "Flutter, Dart, BLoC/Riverpod, animations, and multi-platform deployment.",
        "type": "role", "category": "mobile",
        "role_keywords": ["flutter", "dart", "bloc", "riverpod", "provider", "getx", "widget",
                          "stateful", "stateless", "animation", "material", "cupertino", "pub.dev"],
    },
    {
        "slug": "ios-developer",
        "name": "iOS / Swift Developer",
        "description": "SwiftUI, UIKit, Combine, CoreData, Xcode, and Apple platform development.",
        "type": "role", "category": "mobile",
        "role_keywords": ["swift", "swiftui", "uikit", "combine", "coredata", "xcode", "appkit",
                          "objective-c", "cocoapods", "spm", "instruments", "testflight"],
    },
    # ── Database ──
    {
        "slug": "database",
        "name": "Database Engineer",
        "description": "SQL, NoSQL, query optimization, schema design, and data modeling.",
        "type": "role", "category": "database",
        "role_keywords": ["database", "dba", "sql", "postgres", "postgresql", "mysql", "mongodb",
                          "redis", "sqlite", "schema", "index", "query-optimization", "normalization",
                          "migration", "replication", "sharding", "acid"],
    },
    {
        "slug": "postgres-developer",
        "name": "PostgreSQL Expert",
        "description": "Advanced PostgreSQL: indexing, JSONB, full-text search, partitioning, and tuning.",
        "type": "role", "category": "database",
        "role_keywords": ["postgresql", "postgres", "pgvector", "jsonb", "full-text-search", "tsvector",
                          "partitioning", "pg_trgm", "explain-analyze", "vacuum", "cte", "window-function"],
    },
    # ── Testing ──
    {
        "slug": "testing",
        "name": "QA / Testing Engineer",
        "description": "Unit, integration, E2E testing, TDD, BDD, and quality automation.",
        "type": "role", "category": "testing",
        "role_keywords": ["qa", "testing", "test", "jest", "vitest", "pytest", "mocha", "jasmine",
                          "cypress", "playwright", "selenium", "tdd", "bdd", "coverage", "mock",
                          "fixture", "e2e", "integration", "unit", "contract"],
    },
    # ── Specialized ──
    {
        "slug": "blockchain-developer",
        "name": "Blockchain / Web3 Developer",
        "description": "Smart contracts, Solidity, EVM, DeFi, NFTs, and Web3 tooling.",
        "type": "role", "category": "backend",
        "role_keywords": ["blockchain", "web3", "solidity", "evm", "ethereum", "hardhat", "foundry",
                          "defi", "nft", "smart-contract", "ethers", "wagmi", "viem", "ipfs", "polygon"],
    },
    {
        "slug": "game-developer",
        "name": "Game Developer",
        "description": "Unity, Unreal, game loops, physics, shaders, and game architecture.",
        "type": "role", "category": "other",
        "role_keywords": ["game", "unity", "unreal", "godot", "shader", "physics", "ecs", "gameloop",
                          "sprite", "animation", "collision", "pathfinding", "three.js", "webgl", "babylon"],
    },
    {
        "slug": "embedded-developer",
        "name": "Embedded / IoT Developer",
        "description": "Embedded C/C++, RTOS, microcontrollers, IoT protocols, and hardware interfaces.",
        "type": "role", "category": "other",
        "role_keywords": ["embedded", "iot", "arduino", "raspberry-pi", "rtos", "freertos", "stm32",
                          "mqtt", "bluetooth", "zigbee", "can-bus", "spi", "i2c", "uart", "firmware"],
    },
    {
        "slug": "technical-writer",
        "name": "Technical Writer",
        "description": "API docs, developer guides, doc-as-code, OpenAPI, and documentation tooling.",
        "type": "role", "category": "other",
        "role_keywords": ["technical-writing", "docs", "documentation", "openapi", "swagger",
                          "docusaurus", "mkdocs", "readme", "changelog", "api-docs", "diagramming"],
    },
    {
        "slug": "api-design",
        "name": "API Designer",
        "description": "REST, GraphQL, gRPC, OpenAPI, versioning, and API best practices.",
        "type": "role", "category": "api-design",
        "role_keywords": ["api", "rest", "restful", "graphql", "grpc", "openapi", "swagger", "api-design",
                          "versioning", "hateoas", "rate-limiting", "pagination", "webhook"],
    },
    {
        "slug": "open-source-maintainer",
        "name": "Open Source Maintainer",
        "description": "Release management, semantic versioning, changelogs, community, and OSS tooling.",
        "type": "role", "category": "other",
        "role_keywords": ["open-source", "oss", "semver", "changelog", "release", "contributing",
                          "license", "monorepo", "lerna", "nx", "turbo", "changesets", "community"],
    },
    {
        "slug": "wordpress-developer",
        "name": "WordPress / CMS Developer",
        "description": "WordPress, WooCommerce, themes, plugins, Gutenberg, and CMS development.",
        "type": "role", "category": "frontend",
        "role_keywords": ["wordpress", "woocommerce", "plugin", "theme", "gutenberg", "blocks",
                          "php", "shortcode", "hooks", "wp-cli", "headless", "cms", "contentful", "sanity"],
    },
    {
        "slug": "shopify-developer",
        "name": "Shopify / E-commerce Developer",
        "description": "Shopify, Liquid, storefront API, payments, and e-commerce best practices.",
        "type": "role", "category": "frontend",
        "role_keywords": ["shopify", "liquid", "storefront", "ecommerce", "e-commerce", "cart", "checkout",
                          "payment", "stripe", "subscription", "inventory", "merchant", "theme"],
    },
    {
        "slug": "dx-engineer",
        "name": "Developer Experience Engineer",
        "description": "CLI tools, SDKs, dev tooling, documentation, and making devs productive.",
        "type": "role", "category": "other",
        "role_keywords": ["developer-experience", "dx", "cli", "sdk", "tooling", "scaffold",
                          "linting", "formatting", "eslint", "prettier", "husky", "commitlint", "codegen"],
    },
]

# ── Task Bundles ───────────────────────────────────────────────────────────────

TASK_BUNDLES = [
    {
        "slug": "build-landing-page",
        "name": "Build a Landing Page",
        "description": "Skills for designing and building a high-converting landing page.",
        "type": "task", "category": "frontend",
        "task_keywords": ["landing-page", "website", "design", "conversion", "hero", "cta", "animation"],
    },
    {
        "slug": "setup-cicd",
        "name": "Set Up CI/CD Pipeline",
        "description": "Skills for automating build, test, and deployment workflows.",
        "type": "task", "category": "devops",
        "task_keywords": ["ci-cd", "github-actions", "deployment", "automation", "pipeline", "workflow"],
    },
    {
        "slug": "write-unit-tests",
        "name": "Write Unit Tests",
        "description": "Skills for writing comprehensive unit and integration tests.",
        "type": "task", "category": "testing",
        "task_keywords": ["unit-test", "testing", "jest", "vitest", "pytest", "mock", "coverage"],
    },
    {
        "slug": "design-rest-api",
        "name": "Design a REST API",
        "description": "Skills for designing, documenting, and building RESTful APIs.",
        "type": "task", "category": "api-design",
        "task_keywords": ["rest-api", "api-design", "openapi", "swagger", "endpoints", "versioning"],
    },
    {
        "slug": "setup-auth",
        "name": "Implement Authentication",
        "description": "Skills for adding secure authentication and authorization.",
        "type": "task", "category": "security",
        "task_keywords": ["authentication", "oauth", "jwt", "auth", "login", "session", "passport"],
    },
    {
        "slug": "build-saas",
        "name": "Build a SaaS Product",
        "description": "Full SaaS stack: auth, billing, dashboard, multi-tenancy, and deployment.",
        "type": "task", "category": "fullstack",
        "task_keywords": ["saas", "subscription", "billing", "multi-tenant", "dashboard", "onboarding", "stripe"],
    },
    {
        "slug": "add-payments",
        "name": "Add Payment Processing",
        "description": "Stripe, subscriptions, webhooks, invoices, and billing integrations.",
        "type": "task", "category": "backend",
        "task_keywords": ["payment", "stripe", "subscription", "billing", "invoice", "webhook", "checkout"],
    },
    {
        "slug": "setup-docker",
        "name": "Containerize with Docker",
        "description": "Dockerfile, docker-compose, multi-stage builds, and container best practices.",
        "type": "task", "category": "devops",
        "task_keywords": ["docker", "dockerfile", "compose", "container", "image", "registry", "multi-stage"],
    },
    {
        "slug": "deploy-to-cloud",
        "name": "Deploy to Cloud",
        "description": "Deploy apps to AWS, GCP, Azure, Vercel, Fly.io, or Railway.",
        "type": "task", "category": "cloud",
        "task_keywords": ["deploy", "deployment", "cloud", "aws", "vercel", "fly.io", "railway", "render", "heroku"],
    },
    {
        "slug": "setup-database",
        "name": "Set Up a Database",
        "description": "Schema design, migrations, ORMs, connection pooling, and backup strategies.",
        "type": "task", "category": "database",
        "task_keywords": ["database", "schema", "migration", "orm", "postgres", "mysql", "prisma", "drizzle"],
    },
    {
        "slug": "setup-monitoring",
        "name": "Set Up Monitoring & Observability",
        "description": "Logging, metrics, tracing, dashboards, and alerting for production systems.",
        "type": "task", "category": "devops",
        "task_keywords": ["monitoring", "observability", "logging", "metrics", "tracing", "prometheus",
                          "grafana", "sentry", "datadog", "opentelemetry", "alert", "dashboard"],
    },
    {
        "slug": "optimize-performance",
        "name": "Optimize App Performance",
        "description": "Bundle size, caching, lazy loading, database queries, and rendering performance.",
        "type": "task", "category": "frontend",
        "task_keywords": ["performance", "optimization", "bundle", "lazy-loading", "caching", "lighthouse",
                          "web-vitals", "lcp", "fid", "cls", "profiling", "memoization"],
    },
    {
        "slug": "build-dashboard",
        "name": "Build an Analytics Dashboard",
        "description": "Charts, data visualization, real-time updates, and filtering for dashboards.",
        "type": "task", "category": "frontend",
        "task_keywords": ["dashboard", "analytics", "charts", "visualization", "recharts", "d3",
                          "chart.js", "real-time", "filter", "table", "datatable", "reporting"],
    },
    {
        "slug": "build-chatbot",
        "name": "Build an AI Chatbot",
        "description": "LLM integration, streaming responses, conversation memory, and chat UI.",
        "type": "task", "category": "ml-ai",
        "task_keywords": ["chatbot", "llm", "chat", "streaming", "openai", "claude", "conversation",
                          "memory", "langchain", "vercel-ai", "ai-sdk", "websocket"],
    },
    {
        "slug": "setup-search",
        "name": "Add Full-Text Search",
        "description": "Full-text search, semantic search, Algolia, Elasticsearch, and autocomplete.",
        "type": "task", "category": "backend",
        "task_keywords": ["search", "full-text", "elasticsearch", "algolia", "meilisearch", "typesense",
                          "semantic-search", "vector-search", "autocomplete", "fuzzy", "indexing"],
    },
    {
        "slug": "build-realtime",
        "name": "Add Real-Time Features",
        "description": "WebSockets, SSE, Pusher, Ably, and real-time collaboration patterns.",
        "type": "task", "category": "backend",
        "task_keywords": ["realtime", "real-time", "websocket", "sse", "server-sent-events", "pusher",
                          "ably", "socket.io", "collaboration", "presence", "broadcast", "polling"],
    },
    {
        "slug": "setup-caching",
        "name": "Implement Caching",
        "description": "Redis, CDN caching, HTTP caching, query caching, and cache invalidation.",
        "type": "task", "category": "backend",
        "task_keywords": ["cache", "caching", "redis", "cdn", "http-cache", "etag", "stale-while-revalidate",
                          "invalidation", "ttl", "memcached", "query-cache", "memoize"],
    },
    {
        "slug": "build-cli-tool",
        "name": "Build a CLI Tool",
        "description": "Commander, Inquirer, Yargs, shell scripting, and CLI distribution.",
        "type": "task", "category": "other",
        "task_keywords": ["cli", "command-line", "commander", "yargs", "inquirer", "clack", "shell",
                          "bash", "stdin", "stdout", "ttys", "progress", "spinner", "chalk"],
    },
    {
        "slug": "setup-notifications",
        "name": "Set Up Notifications",
        "description": "Push notifications, email, SMS, in-app alerts, and notification systems.",
        "type": "task", "category": "backend",
        "task_keywords": ["notification", "push", "email", "sms", "sendgrid", "resend", "twilio",
                          "firebase-fcm", "apns", "toast", "in-app", "webhook", "novu"],
    },
    {
        "slug": "setup-file-storage",
        "name": "Set Up File Storage & Uploads",
        "description": "S3, Cloudflare R2, multipart uploads, CDN delivery, and media processing.",
        "type": "task", "category": "cloud",
        "task_keywords": ["file-storage", "upload", "s3", "r2", "cloudflare", "multipart", "presigned",
                          "cdn", "imagekit", "cloudinary", "media", "resize", "compress"],
    },
    {
        "slug": "add-rate-limiting",
        "name": "Add Rate Limiting & Security",
        "description": "API rate limiting, bot protection, CORS, helmet, and request validation.",
        "type": "task", "category": "security",
        "task_keywords": ["rate-limiting", "throttle", "cors", "helmet", "csrf", "bot-protection",
                          "input-validation", "sanitize", "ddos", "waf", "ip-block", "captcha"],
    },
    {
        "slug": "build-graphql-api",
        "name": "Build a GraphQL API",
        "description": "GraphQL schema, resolvers, subscriptions, federation, and client integration.",
        "type": "task", "category": "api-design",
        "task_keywords": ["graphql", "schema", "resolver", "mutation", "subscription", "federation",
                          "apollo", "urql", "codegen", "dataloader", "relay", "hasura", "nexus"],
    },
    {
        "slug": "migrate-to-typescript",
        "name": "Migrate to TypeScript",
        "description": "TypeScript setup, type safety, generics, utility types, and migration patterns.",
        "type": "task", "category": "frontend",
        "task_keywords": ["typescript", "type-safety", "generics", "utility-types", "tsconfig", "strict",
                          "declaration", "module", "namespace", "interface", "type-guard", "zod"],
    },
]


def _dedup_parent_child(skills: list[Skill]) -> list[Skill]:
    """Remove parent repo slugs when a child skill from the same repo is already in the list."""
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
        """
        Fetch top skills for a bundle.
        Strategy:
        1. Try keyword match (role_keywords OR task_keywords) across name/tags/role_keywords/task_keywords
        2. Fall back to category-only if insufficient results
        """
        keywords = (role_keywords or []) + (task_keywords or [])

        # Category filter — fullstack pulls from multiple categories
        if category == "fullstack":
            cat_filter = Skill.primary_category.in_(["frontend", "backend", "database", "fullstack"])
        elif category in ("other", "api-design"):
            # broad match — don't restrict by category when it's a cross-cutting concern
            cat_filter = None
        else:
            cat_filter = Skill.primary_category == category

        base_filters = [
            Skill.is_active == True,
            Skill.tier == 1,
            Skill.quality_score >= 4,
        ]
        if cat_filter is not None:
            base_filters.append(cat_filter)

        # ── Pass 1: keyword match ────────────────────────────────────────────
        skills: list[Skill] = []
        if keywords:
            kw_conditions = [
                or_(
                    func.lower(Skill.name).contains(kw.lower()),
                    func.lower(Skill.description).contains(kw.lower()),
                    func.array_to_string(Skill.role_keywords, ' ').ilike(f'%{kw}%'),
                    func.array_to_string(Skill.task_keywords, ' ').ilike(f'%{kw}%'),
                    func.array_to_string(Skill.tags, ' ').ilike(f'%{kw}%'),
                )
                for kw in keywords[:12]  # cap at 12 keywords for query perf
            ]
            skills = (
                self.db.query(Skill)
                .filter(*base_filters, or_(*kw_conditions))
                .order_by((Skill.quality_score * 0.6 + Skill.popularity_score * 0.4).desc())
                .limit(limit * 2)
                .all()
            )

        # ── Pass 2: category fallback if not enough ──────────────────────────
        if len(skills) < 15:
            existing_ids = {s.id for s in skills}
            fallback_filters = [
                Skill.is_active == True,
                Skill.tier == 1,
                Skill.quality_score >= 3,
            ]
            if cat_filter is not None:
                fallback_filters.append(cat_filter)
            extra = (
                self.db.query(Skill)
                .filter(*fallback_filters)
                .order_by((Skill.quality_score * 0.6 + Skill.popularity_score * 0.4).desc())
                .limit(limit)
                .all()
            )
            skills.extend([s for s in extra if s.id not in existing_ids])

        skills = _dedup_parent_child(skills)
        return skills[:limit]

    def _upsert_bundle(self, bundle_def: dict, skill_ids: list[int]) -> Bundle:
        existing = self.db.query(Bundle).filter_by(slug=bundle_def["slug"]).first()
        if existing:
            existing.skill_ids   = skill_ids
            existing.skill_count = len(skill_ids)
            existing.name        = bundle_def["name"]
            existing.description = bundle_def["description"]
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
        self.db.query(BundleCommand).filter_by(bundle_id=bundle.id).delete()
        self.db.commit()
        platforms = ["claude_code", "cursor", "copilot", "continue", "universal"]
        for platform in platforms:
            cmd = self.install_gen.generate(skills, platform, bundle.slug)
            self.db.add(BundleCommand(bundle_id=bundle.id, platform=platform, command=cmd))
        self.db.commit()

    def generate_all(self):
        """Generate all role + task bundles (50+)."""
        all_defs = ROLE_BUNDLES + TASK_BUNDLES
        total = len(all_defs)
        print(f"[blue]Generating {total} bundles...[/blue]")

        generated, skipped = 0, 0
        for i, bundle_def in enumerate(all_defs):
            skills = self._get_skills_for_bundle(
                category=bundle_def.get("category", "other"),
                role_keywords=bundle_def.get("role_keywords"),
                task_keywords=bundle_def.get("task_keywords"),
                limit=30,
            )
            if not skills:
                print(f"[yellow]  [{i+1}/{total}] '{bundle_def['slug']}': no skills, skipping.[/yellow]")
                skipped += 1
                continue

            skill_ids = [s.id for s in skills]
            bundle = self._upsert_bundle(bundle_def, skill_ids)
            self._generate_commands(bundle, skills)
            print(f"[green]  [{i+1}/{total}] '{bundle.slug}': {len(skills)} skills[/green]")
            generated += 1

        print(f"[bold green]Done: {generated} bundles generated, {skipped} skipped (no skills).[/bold green]")
