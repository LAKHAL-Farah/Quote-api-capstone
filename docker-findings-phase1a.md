# Phase 1a findings — naive Dockerfile

## Image size
quote-api:naive size: [paste the actual number from `docker images` here]

## Cache invalidation
Touching app/main.py (a one-line comment, zero dependency changes)
caused `RUN pip install -r requirements.txt` to re-run from scratch.
Root cause: COPY . . runs before RUN pip install, so any file change
invalidates every layer after it, regardless of relevance.

## SIGTERM handling
docker stop took ~10 seconds (full grace period + SIGKILL).
Root cause: shell-form CMD makes /bin/sh PID 1, not uvicorn.
SIGTERM goes to PID 1 (sh), which doesn't forward it to uvicorn,
so Docker eventually force-kills via SIGKILL instead of a clean exit.
Verified via `docker exec ... ps aux` — PID 1 was /bin/sh, not uvicorn.


## Phase 1b — fixes applied

### Image size
quote-api:naive size: [your Phase 1a number]
quote-api:latest size: [paste new number from `docker images quote-api:latest`]
Reduction: [calculate the percentage]

Root cause was a single-stage build using the full python:3.11 base image,
which includes build tools never needed at runtime. Fixed with a multi-stage
build — stage 1 (builder) installs dependencies with full build tools available;
stage 2 (production) starts from python:3.11-slim and copies in only the
installed packages via COPY --from=builder, never including the compiler
toolchain in the final image.

### Cache invalidation
Before: touching app/main.py caused a full pip reinstall every time.
After: same change now hits the Docker build cache for the pip install layer
(confirmed via `docker build` output showing CACHED), because requirements.txt
is COPYed and installed BEFORE application code, so app code changes never
invalidate the dependency layer.

### SIGTERM handling
Before: docker stop took ~10s (full grace period + SIGKILL). PID 1 was
/bin/sh, confirmed via `docker exec ... ps aux`.
After: docker stop completes in under 1 second. PID 1 is now uvicorn directly,
confirmed via the same ps aux check. Root cause was shell-form CMD; fixed by
switching to exec-form CMD ["uvicorn", ...].

### Additional hardening applied (not part of the original 3 problems)
- Non-root user (appuser, uid 1001) — confirmed via `docker run --rm ... whoami`
- HEALTHCHECK calling the app's own /health endpoint — confirmed container
  shows (healthy) status in `docker ps` after the start_period grace window

---

## Phase 3 — Compose startup race condition

### Symptom
On `docker compose down -v && docker compose up` (forcing a fresh Postgres
volume initialization), the api container would start and attempt a database
connection before Postgres had finished its first-time initialization,
sometimes intermittently rather than every time.

### Root cause
`depends_on: - db` (list form) only guarantees the db CONTAINER has started,
not that the Postgres PROCESS inside it is actually ready to accept
connections. These are different moments, especially during first-time
volume initialization.

### Fix
Added a `healthcheck` to the db service using `pg_isready` (Postgres's own
readiness probe), and changed api's `depends_on` to the object form:
`depends_on: db: condition: service_healthy`. Confirmed via `docker compose ps`
that api does not start until db's status shows `(healthy)`.

### Additional verification
Confirmed named volumes persist data across `docker compose down` (no -v),
and confirmed `-v` correctly wipes the volume — verified both behaviors
directly rather than assuming.

---

## Phase 4 — Stale cache data

### Symptom
After caching a quote via GET /quote/{id}, updating that quote's text
directly in Postgres (bypassing the API) resulted in the API continuing
to serve the old, cached text indefinitely.

### Root cause
The initial caching implementation stored values in Redis with no
expiry (`r.set()` with no `ex` parameter) — once cached, a value had
no mechanism to ever be considered stale.

### Fix
1. Added a TTL (5 minutes, +/- 30s jitter to avoid synchronized mass
   expiry / thundering herd) to every cache write.
2. Added explicit `invalidate_quote_cache()` calls on the API's own
   write paths (PUT, DELETE) so writes through the API self-correct
   immediately rather than waiting out the TTL.

### Documented limitation
Writes that bypass the API entirely (e.g. a direct SQL UPDATE) are
NOT caught by explicit invalidation, since the API never sees them.
The TTL is what bounds staleness in that case — confirmed by testing
with a shortened TTL (10s) and confirming the API self-corrected after
the TTL expired, with no application code change required.
