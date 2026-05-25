# Phase 6 — Batch Queue

**Status:** not started  
**Depends on:** [Phase 5](./05-orchestrator-api.md) (**blocker** — need `runner` + `/api/v1/enhance` first)  
**Parallel with:** —

---

## Goal

Process many images asynchronously with job status — drop files in `data/input/`, poll for completion.

---

## Scope IN

- Add `redis` service to compose
- Job model: `pending | running | completed | failed` with `{ id, input, output, error, stages }`
- `POST /api/v1/jobs` — enqueue (single file or directory scan)
- `GET /api/v1/jobs/{id}` — status
- `GET /api/v1/jobs` — list recent jobs
- Worker process: `python -m app.worker` (same orchestrator image, different command)
- CLI: `python -m app.cli batch --input-dir /data/input/`
- Concurrency: 1 job at a time for ComfyUI (configurable `MAX_CONCURRENT_JOBS`)

## Scope OUT

- Web UI
- Priority queues
- Horizontal scaling multiple ComfyUI replicas

---

## Design

```
POST /jobs → Redis queue → worker pulls → pipeline.runner.run() → update job status
```

- Redis keys: `photo-ai:job:{id}`, `photo-ai:queue`
- TTL on completed jobs (default 7 days)
- Failed jobs retain artifact paths for debug

---

## Verification

```bash
docker compose up -d
cp tests/fixtures/*.jpg data/input/
curl -X POST http://localhost:8090/api/v1/jobs \
  -F "input_dir=/data/input"
# Returns job_id

curl http://localhost:8090/api/v1/jobs/{job_id}
# Eventually status=completed, outputs listed

docker compose exec orchestrator python -m app.cli batch --input-dir /data/input
```

---

## Done when

- [ ] Redis healthy in compose
- [ ] Worker container/process consumes queue
- [ ] Batch of 3+ images completes sequentially
- [ ] Job status API accurate through lifecycle
- [ ] OOM/failure marks job failed without blocking queue forever
- [ ] README documents batch workflow

---

## Agent notes

- Use redis-py or arq/RQ — pick simplest; avoid Celery unless needed.
- ComfyUI must stay single-flight unless you add locking — document this.
