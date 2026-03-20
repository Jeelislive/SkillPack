# SkillPack Pipeline Reference

## Pipeline Flow
```
run_crawl.py
  ├── skills_sh_scraper.py  → scrapes skills.sh /api/skills
  ├── github_crawler.py     → searches GitHub topic:claude-skill
  ├── tagger.py             → Groq LLM batches → primary_category, tags, quality_score
  ├── ingestion.py          → bulk_insert_mappings → skills table (Tier 1 only)
  └── bundle_generator.py  → keyword pre-filter → AI/manual curation → BundleCommand rows
```

## Key Files
- `backend/run_crawl.py` - entrypoint, CLI flags: `--test`, `bundles`
- `backend/pipeline/tagger.py` - Groq LLM tagging (batches of 20)
- `backend/pipeline/bundle_generator.py` - 50+ bundle definitions + AI curation
- `backend/pipeline/manual_bundle_curator.py` - Claude-curated bundles (no Groq)
- `backend/pipeline/install_generator.py` - generates npx install commands
- `backend/db/ingestion.py` - bulk upsert via bulk_insert_mappings

## Tier 1 Qualification
- `quality_score >= 5` AND `install_count >= TIER1_MIN_INSTALLS` (default 10)
- `TIER1_MAX_SKILLS = 25000` - cap to prevent DB bloat
- Below threshold → `skills_index` (Tier 2, live-fetched from GitHub)

## Adding a New Skill Source
1. Create scraper in `pipeline/` returning list of `dict` with: `slug`, `name`, `description`, `raw_content`, `source_url`, `platforms`
2. Call `tagger.tag_skills(skills)` to assign categories/quality scores
3. Call `ingestion.ingest_skills(skills, db)` to bulk upsert
4. Slug format: `owner/repo` (GitHub) or `owner/repo/skillId` (skills.sh)

## Modifying the Tagger Prompt
- File: `pipeline/tagger.py` - look for `_TAGGER_PROMPT`
- Categories must be one of: `frontend, backend, fullstack, devops, ml-ai, security, database, testing, cloud, mobile, data-science`
- Falls back to keyword heuristics if Groq fails/rate-limits
- Batch size: 20 skills per Groq call

## Adding a New Bundle
In `pipeline/bundle_generator.py`:
```python
{
    "slug": "my-bundle",
    "name": "My Bundle Name",
    "description": "What this bundle covers.",
    "type": "role",  # or "task"
    "category": "backend",  # primary category for filtering
    "role_keywords": ["keyword1", "keyword2", ...],  # for keyword pre-filter
},
```
Or for manual curation, add to `pipeline/manual_bundle_curator.py` CURATED_BUNDLES dict.

## Regenerating Bundles Only
```bash
python3 run_crawl.py bundles          # uses Groq AI curation
python3 -m pipeline.manual_bundle_curator  # uses manually curated skill IDs
```

## Content Dedup
- `ingestion.py` computes `content_hash = md5(raw_content)`
- If hash matches existing row → skip re-tagging (no Groq API call)
- Change content → new hash → re-tags on next crawl

## Groq Rate Limits
- Free tier: ~30 RPM → `time.sleep(1.5)` between bundle AI calls
- Model: `llama-3.3-70b-versatile` (set in `.env` GROQ_MODEL)
- If rate-limited → falls back to keyword-filtered candidates (no AI filter)

## Debugging Pipeline Failures
1. Check `CrawlJob` rows: `SELECT * FROM crawl_jobs ORDER BY started_at DESC LIMIT 5;`
2. Check skill count: `SELECT COUNT(*), primary_category FROM skills WHERE tier=1 GROUP BY primary_category;`
3. Check bundle skill counts: `SELECT slug, skill_count FROM bundles ORDER BY skill_count DESC;`
4. Manual tagger test: `python3 -c "from pipeline.tagger import tag_skills; ..."`
