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
