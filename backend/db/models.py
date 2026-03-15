from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Numeric,
    ARRAY, TIMESTAMP, SmallInteger, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.database import Base


class Source(Base):
    __tablename__ = "sources"

    id              = Column(Integer, primary_key=True)
    name            = Column(String, nullable=False, unique=True)
    display_name    = Column(String, nullable=False)
    base_url        = Column(String)
    crawl_strategy  = Column(String, nullable=False)
    total_skills    = Column(Integer, default=0)
    last_crawled_at = Column(TIMESTAMP(timezone=True))
    last_success_at = Column(TIMESTAMP(timezone=True))
    is_active       = Column(Boolean, default=True)
    created_at      = Column(TIMESTAMP(timezone=True), server_default=func.now())

    skills     = relationship("Skill", back_populates="source")
    crawl_jobs = relationship("CrawlJob", back_populates="source")


class Skill(Base):
    __tablename__ = "skills"

    id               = Column(Integer, primary_key=True)
    source_id        = Column(Integer, ForeignKey("sources.id"))

    # Identity
    owner            = Column(String, nullable=False)
    repo             = Column(String, nullable=False)
    slug             = Column(String, nullable=False, unique=True)  # owner/repo
    name             = Column(String, nullable=False)
    description      = Column(Text)

    # Content
    raw_content      = Column(Text)
    content_hash     = Column(String)

    # Classification (set by AI)
    primary_category = Column(String)
    sub_categories   = Column(ARRAY(String), default=[])
    tags             = Column(ARRAY(String), default=[])
    role_keywords    = Column(ARRAY(String), default=[])
    task_keywords    = Column(ARRAY(String), default=[])

    # Platform compatibility
    platforms        = Column(ARRAY(String), default=[])
    install_command  = Column(Text)

    # Quality signals
    quality_score    = Column(Numeric(4, 2), default=0)
    popularity_score = Column(Numeric(4, 2), default=0)
    install_count    = Column(Integer, default=0)
    github_stars     = Column(Integer, default=0)
    content_length   = Column(Integer, default=0)

    # Tier
    tier             = Column(SmallInteger, default=1)
    is_active        = Column(Boolean, default=True)

    source_url       = Column(Text)
    raw_url          = Column(Text)
    published_at     = Column(TIMESTAMP(timezone=True))
    last_crawled_at  = Column(TIMESTAMP(timezone=True), server_default=func.now())
    created_at       = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at       = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    source = relationship("Source", back_populates="skills")


class SkillIndex(Base):
    __tablename__ = "skills_index"

    id              = Column(Integer, primary_key=True)
    source_id       = Column(Integer, ForeignKey("sources.id"))
    slug            = Column(String, nullable=False, unique=True)
    name            = Column(String)
    description     = Column(Text)
    raw_url         = Column(Text, nullable=False)
    install_command = Column(Text)
    platforms       = Column(ARRAY(String), default=[])
    install_count   = Column(Integer, default=0)
    github_stars    = Column(Integer, default=0)
    last_seen_at    = Column(TIMESTAMP(timezone=True), server_default=func.now())
    created_at      = Column(TIMESTAMP(timezone=True), server_default=func.now())


class Bundle(Base):
    __tablename__ = "bundles"

    id            = Column(Integer, primary_key=True)
    slug          = Column(String, nullable=False, unique=True)
    name          = Column(String, nullable=False)
    description   = Column(Text)
    type          = Column(String, nullable=False)   # 'role', 'task', 'micro'
    category      = Column(String)
    skill_ids     = Column(ARRAY(Integer), default=[])
    skill_count   = Column(Integer, default=0)
    install_count = Column(Integer, default=0)
    is_featured   = Column(Boolean, default=False)
    is_active     = Column(Boolean, default=True)
    created_by    = Column(String, default="system")
    created_at    = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at    = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    commands = relationship("BundleCommand", back_populates="bundle", cascade="all, delete")


class BundleCommand(Base):
    __tablename__ = "bundle_commands"

    id         = Column(Integer, primary_key=True)
    bundle_id  = Column(Integer, ForeignKey("bundles.id", ondelete="CASCADE"))
    platform   = Column(String, nullable=False)  # 'claude_code', 'cursor', 'copilot', 'continue', 'universal'
    command    = Column(Text, nullable=False)
    script_url = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    bundle = relationship("Bundle", back_populates="commands")


class CrawlJob(Base):
    __tablename__ = "crawl_jobs"

    id             = Column(Integer, primary_key=True)
    source_id      = Column(Integer, ForeignKey("sources.id"))
    status         = Column(String, default="pending")
    skills_found   = Column(Integer, default=0)
    skills_added   = Column(Integer, default=0)
    skills_updated = Column(Integer, default=0)
    errors         = Column(JSON, default=[])
    started_at     = Column(TIMESTAMP(timezone=True))
    finished_at    = Column(TIMESTAMP(timezone=True))
    created_at     = Column(TIMESTAMP(timezone=True), server_default=func.now())

    source = relationship("Source", back_populates="crawl_jobs")
