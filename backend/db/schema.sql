-- Enable extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS unaccent;

-- ──────────────────────────────────────────
-- SOURCES
-- ──────────────────────────────────────────
CREATE TABLE sources (
    id              SERIAL PRIMARY KEY,
    name            TEXT NOT NULL UNIQUE,          -- 'skills_sh', 'github', 'microsoft', 'cursor', 'continue', 'mcp'
    display_name    TEXT NOT NULL,
    base_url        TEXT,
    crawl_strategy  TEXT NOT NULL,                 -- 'scrape', 'api', 'git'
    total_skills    INTEGER DEFAULT 0,
    last_crawled_at TIMESTAMPTZ,
    last_success_at TIMESTAMPTZ,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ──────────────────────────────────────────
-- SKILLS (Tier 1 - stored, high quality)
-- ──────────────────────────────────────────
CREATE TABLE skills (
    id                  SERIAL PRIMARY KEY,
    source_id           INTEGER REFERENCES sources(id),

    -- Identity
    owner               TEXT NOT NULL,             -- GitHub owner
    repo                TEXT NOT NULL,             -- GitHub repo name
    slug                TEXT NOT NULL UNIQUE,      -- owner/repo
    name                TEXT NOT NULL,
    description         TEXT,

    -- Content (stored, TOAST-compressed automatically)
    raw_content         TEXT,                      -- full SKILL.md content
    content_hash        TEXT,                      -- MD5 of raw_content for change detection

    -- Classification (set by AI pipeline)
    primary_category    TEXT,                      -- 'frontend', 'backend', 'devops', etc.
    sub_categories      TEXT[],                    -- ['css', 'animation', 'typography']
    tags                TEXT[],                    -- free-form tags
    role_keywords       TEXT[],                    -- ['frontend developer', 'ui engineer']
    task_keywords       TEXT[],                    -- ['build landing page', 'animate elements']

    -- Platform compatibility
    platforms           TEXT[],                    -- ['claude_code', 'cursor', 'copilot', 'continue']
    install_command     TEXT,                      -- npx skills add owner/repo

    -- Quality signals
    quality_score       NUMERIC(4,2) DEFAULT 0,   -- 0-10, set by AI
    popularity_score    NUMERIC(4,2) DEFAULT 0,   -- 0-10, from install_count + stars
    install_count       INTEGER DEFAULT 0,
    github_stars        INTEGER DEFAULT 0,
    content_length      INTEGER DEFAULT 0,

    -- Tier
    tier                SMALLINT DEFAULT 1,        -- 1=stored, 2=live-fetch only
    is_active           BOOLEAN DEFAULT TRUE,

    -- Timestamps
    source_url          TEXT,
    raw_url             TEXT,                      -- direct URL to fetch SKILL.md (for tier 2)
    published_at        TIMESTAMPTZ,
    last_crawled_at     TIMESTAMPTZ DEFAULT NOW(),
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

-- ──────────────────────────────────────────
-- SKILL INDEX (Tier 2 - metadata only, live fetch)
-- ──────────────────────────────────────────
CREATE TABLE skills_index (
    id              SERIAL PRIMARY KEY,
    source_id       INTEGER REFERENCES sources(id),
    slug            TEXT NOT NULL UNIQUE,          -- owner/repo
    name            TEXT,
    description     TEXT,
    raw_url         TEXT NOT NULL,                 -- URL to fetch SKILL.md on demand
    install_command TEXT,
    platforms       TEXT[],
    install_count   INTEGER DEFAULT 0,
    github_stars    INTEGER DEFAULT 0,
    last_seen_at    TIMESTAMPTZ DEFAULT NOW(),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ──────────────────────────────────────────
-- BUNDLES
-- ──────────────────────────────────────────
CREATE TABLE bundles (
    id              SERIAL PRIMARY KEY,
    slug            TEXT NOT NULL UNIQUE,          -- 'frontend', 'backend-nodejs', 'devops-aws'
    name            TEXT NOT NULL,
    description     TEXT,
    type            TEXT NOT NULL,                 -- 'role', 'task', 'micro'
    category        TEXT,                          -- matches primary_category
    skill_ids       INTEGER[],                     -- ordered list of skill IDs
    skill_count     INTEGER DEFAULT 0,
    install_count   INTEGER DEFAULT 0,
    is_featured     BOOLEAN DEFAULT FALSE,
    is_active       BOOLEAN DEFAULT TRUE,
    created_by      TEXT DEFAULT 'system',         -- 'system' or user id later
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ──────────────────────────────────────────
-- BUNDLE INSTALL COMMANDS (per platform)
-- ──────────────────────────────────────────
CREATE TABLE bundle_commands (
    id          SERIAL PRIMARY KEY,
    bundle_id   INTEGER REFERENCES bundles(id) ON DELETE CASCADE,
    platform    TEXT NOT NULL,                     -- 'claude_code', 'cursor', 'copilot', 'continue', 'universal'
    command     TEXT NOT NULL,                     -- the actual install command string
    script_url  TEXT,                              -- optional hosted script URL
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(bundle_id, platform)
);

-- ──────────────────────────────────────────
-- CRAWL JOBS
-- ──────────────────────────────────────────
CREATE TABLE crawl_jobs (
    id              SERIAL PRIMARY KEY,
    source_id       INTEGER REFERENCES sources(id),
    status          TEXT DEFAULT 'pending',        -- 'pending', 'running', 'done', 'failed'
    skills_found    INTEGER DEFAULT 0,
    skills_added    INTEGER DEFAULT 0,
    skills_updated  INTEGER DEFAULT 0,
    errors          JSONB DEFAULT '[]',
    started_at      TIMESTAMPTZ,
    finished_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ──────────────────────────────────────────
-- INDEXES (performance)
-- ──────────────────────────────────────────
CREATE INDEX idx_skills_primary_category ON skills(primary_category);
CREATE INDEX idx_skills_quality ON skills(quality_score DESC, popularity_score DESC);
CREATE INDEX idx_skills_tier ON skills(tier);
CREATE INDEX idx_skills_platforms ON skills USING GIN(platforms);
CREATE INDEX idx_skills_tags ON skills USING GIN(tags);
CREATE INDEX idx_skills_sub_categories ON skills USING GIN(sub_categories);
CREATE INDEX idx_skills_role_keywords ON skills USING GIN(role_keywords);

-- Full-text search index (only immutable expressions allowed in GIN index)
CREATE INDEX idx_skills_fts ON skills USING GIN(
    to_tsvector('english',
        COALESCE(name, '') || ' ' ||
        COALESCE(description, '') || ' ' ||
        COALESCE(primary_category, '')
    )
);

-- Trigram index for fuzzy search
CREATE INDEX idx_skills_name_trgm ON skills USING GIN(name gin_trgm_ops);
CREATE INDEX idx_skills_desc_trgm ON skills USING GIN(description gin_trgm_ops);

CREATE INDEX idx_bundles_type ON bundles(type);
CREATE INDEX idx_bundles_category ON bundles(category);
CREATE INDEX idx_skills_index_slug ON skills_index(slug);

-- ──────────────────────────────────────────
-- SEED SOURCES
-- ──────────────────────────────────────────
INSERT INTO sources (name, display_name, base_url, crawl_strategy) VALUES
    ('skills_sh',   'skills.sh',          'https://skills.sh',                          'scrape'),
    ('github',      'GitHub Search',      'https://api.github.com',                     'api'),
    ('microsoft',   'Microsoft Skills',   'https://github.com/microsoft/skills',        'git'),
    ('cursor',      'Cursor Rules',       'https://cursor.directory',                   'scrape'),
    ('continue',    'Continue.dev Hub',   'https://hub.continue.dev',                   'api'),
    ('mcp',         'MCP Registry',       'https://github.com/modelcontextprotocol',    'api');
