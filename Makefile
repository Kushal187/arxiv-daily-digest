WORKER_BASE_URL ?= http://localhost:8000

.PHONY: backfill-history

backfill-history:
	@WORKER_BASE_URL="$(WORKER_BASE_URL)" ./scripts/backfill-history.sh
