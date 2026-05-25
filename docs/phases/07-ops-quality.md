# Phase 7 — Ops, Quality Gates & Presets

**Status:** not started  
**Depends on:** [Phase 6](./06-batch-queue.md)  
**Parallel with:** —

---

## Goal

Production polish: input validation, aesthetic presets, observability, and operator runbook.

---

## Scope IN

- **Preflight checks** before pipeline:
  - Min resolution (e.g. 512px short edge)
  - Max file size (e.g. 30MB)
  - Allowed formats: JPEG, PNG, WebP
  - Blur detection (optional Laplacian variance threshold) → warn or reject
- **Aesthetic presets** — config maps name → prompt suffixes:
  - `minimal`, `luxury`, `lifestyle`, `studio`, `dark` (from guide §4.3)
- **Review flag** — jobs where SD denoise was applied get `needs_review: true` in response
- Structured logging (JSON logs: job_id, stage, duration_ms)
- `GET /metrics` or Prometheus-friendly counters (jobs_total, stage_duration)
- Runbook: `docs/runbook.md` — common failures from guide §7
- Optional: API key header `X-API-Key` for orchestrator

## Scope OUT

- Full web review UI
- Auto color-correction without human review
- Kubernetes manifests

### Candidates from phases 1–4 learnings

- rembg: auto-detect bad mask / wrong output size → suggest or fallback to `u2net`
- rembg: optional crop-to-alpha-bbox after cloth_seg
- upscale: preflight weight file size before load
- Document operator runbook entries for corrupt `.pth` and Docker OOM (137)

---

## Quality rules

| Check | Action |
|-------|--------|
| Short edge < 512px | Reject with `INVALID_INPUT` |
| Blur score below threshold | Warn in response; still process if `--force` |
| SD denoise > 0.35 | Reject unless `allow_high_denoise=true` |
| rembg empty mask | Fail stage with hint to try `u2net_cloth_seg` |

---

## Verification

```bash
# Reject tiny image
curl -X POST http://localhost:8090/api/v1/enhance -F "file=@tests/fixtures/tiny.png"
# Expect 400

# Preset
curl -X POST http://localhost:8090/api/v1/enhance \
  -F "file=@data/input/sample.jpg" \
  -F "aesthetic=luxury"

# Metrics
curl http://localhost:8090/metrics
```

---

## Done when

- [ ] Preflight rejects bad inputs with clear errors
- [ ] All 5 aesthetic presets configurable via YAML/JSON config
- [ ] Runbook covers §7 issues from original guide
- [ ] Logs include structured fields for grep
- [ ] `needs_review` flag on generative stages
- [ ] README links to runbook

---

## Agent notes

- Presets are **prompt token swaps only** — no new pipeline stages.
- Keep runbook operational — copy fixes from guide, not essays.
