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
