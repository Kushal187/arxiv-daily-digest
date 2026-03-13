create extension if not exists pgcrypto;
create extension if not exists vector;

create table if not exists users (
  id uuid primary key default gen_random_uuid(),
  email text not null unique,
  name text,
  image text,
  provider_subject text unique,
  onboarding_completed boolean not null default false,
  preferred_categories text[] not null default '{}',
  profile_embedding vector(384),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists user_topic_preferences (
  user_id uuid not null references users(id) on delete cascade,
  topic_slug text not null,
  weight real not null default 1,
  created_at timestamptz not null default now(),
  primary key (user_id, topic_slug)
);

create table if not exists user_followed_authors (
  user_id uuid not null references users(id) on delete cascade,
  author_name text not null,
  created_at timestamptz not null default now(),
  primary key (user_id, author_name)
);

create index if not exists user_topic_preferences_user_id_idx on user_topic_preferences (user_id);
create index if not exists user_followed_authors_user_id_idx on user_followed_authors (user_id);

create table if not exists papers (
  id uuid primary key default gen_random_uuid(),
  canonical_arxiv_id text not null,
  arxiv_version integer not null,
  source_id text not null unique,
  title text not null,
  abstract text not null,
  authors text[] not null default '{}',
  categories text[] not null default '{}',
  primary_category text not null,
  published_at timestamptz not null,
  updated_at timestamptz not null,
  url text not null,
  embedding vector(384),
  ingest_date date not null,
  classifier_metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique (canonical_arxiv_id, arxiv_version)
);

create index if not exists papers_ingest_date_idx on papers (ingest_date desc);
create index if not exists papers_published_at_idx on papers (published_at desc);
create index if not exists papers_embedding_hnsw_idx
  on papers
  using hnsw (embedding vector_cosine_ops);

create table if not exists paper_authors (
  paper_id uuid not null references papers(id) on delete cascade,
  author_name text not null,
  author_position integer not null,
  primary key (paper_id, author_position)
);

create index if not exists paper_authors_name_idx on paper_authors (author_name);

create table if not exists paper_topics (
  paper_id uuid not null references papers(id) on delete cascade,
  topic_slug text not null,
  confidence real not null,
  is_hidden boolean not null default false,
  source text not null default 'weak-label',
  primary key (paper_id, topic_slug)
);

create index if not exists paper_topics_slug_idx on paper_topics (topic_slug);

create table if not exists paper_clusters (
  paper_id uuid primary key references papers(id) on delete cascade,
  cluster_date date not null,
  cluster_id text not null,
  cluster_label text not null,
  created_at timestamptz not null default now()
);

create index if not exists paper_clusters_date_idx on paper_clusters (cluster_date desc);

create table if not exists user_interactions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id) on delete cascade,
  paper_id uuid not null references papers(id) on delete cascade,
  interaction_type text not null check (interaction_type in ('open', 'save', 'dismiss')),
  created_at timestamptz not null default now(),
  unique (user_id, paper_id, interaction_type)
);

create index if not exists user_interactions_user_type_idx
  on user_interactions (user_id, interaction_type, created_at desc);

create table if not exists job_runs (
  id uuid primary key default gen_random_uuid(),
  job_name text not null,
  run_date date not null,
  status text not null check (status in ('started', 'succeeded', 'failed')),
  started_at timestamptz not null default now(),
  completed_at timestamptz,
  metadata jsonb not null default '{}'::jsonb,
  unique (job_name, run_date)
);

create table if not exists paper_summaries (
  paper_id uuid primary key references papers(id) on delete cascade,
  provider text not null,
  model text not null,
  content text not null,
  created_at timestamptz not null default now()
);
