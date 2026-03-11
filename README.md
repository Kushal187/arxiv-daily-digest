# arxiv-daily-digest

Personalized daily arXiv discovery for ML researchers.

## Monorepo layout

- `apps/web`: Next.js product UI and public API routes.
- `apps/worker`: FastAPI worker for ingestion, ranking, and internal APIs.
- `packages/shared`: shared TypeScript contracts and taxonomy constants.
- `db/schema.sql`: Postgres schema with `pgvector`.

## Architecture

- `Next.js` runs on Vercel and handles auth, onboarding, settings, saved papers, and proxy routes.
- `FastAPI` runs as a worker service and owns ingestion, embeddings, topic labeling, clustering, and ranking.
- `Neon Postgres + pgvector` stores papers, user preferences, interactions, and cached summaries.
- `GitHub Actions` triggers the daily ingest job.

## Local setup

1. Copy `.env.example` into `apps/web/.env.local` and `apps/worker/.env`.
2. Apply `db/schema.sql` to a Postgres database with the `vector` extension enabled.
3. Install workspace dependencies with `npm install`.
4. Install worker dependencies with `python3 -m pip install -e apps/worker`.
5. Start the web app with `npm run dev:web`.
6. Start the worker with `npm run dev:worker`.

## Notes

- The worker falls back to deterministic hashed embeddings when `sentence-transformers` is unavailable.
- Topic labels and recommendation reasons are deterministic. LLM summaries are behind a feature flag.
- Optional paper explanations use Amazon Bedrock's OpenAI-compatible Chat Completions API. The default model is `Qwen3 32B`; set `BEDROCK_API_KEY` and optionally override `SUMMARY_MODEL` or `BEDROCK_BASE_URL`.

## GitHub Actions setup

The scheduled ingest workflow needs these GitHub repository settings:

- Actions variable: `WORKER_BASE_URL`
- Actions secret: `INGEST_JOB_TOKEN`

`WORKER_BASE_URL` should be the public base URL for the worker service, for example `https://your-worker.example.com`.

`INGEST_JOB_TOKEN` must match the worker's `INGEST_JOB_TOKEN` environment variable, or another token accepted by the worker such as `WORKER_INTERNAL_TOKEN`.
