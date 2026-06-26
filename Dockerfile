# _____Stage 1 : Builder_______________
FROM python:3.11 AS Builder
WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade "pip>=26.1" "setuptools>=82.0.1" "wheel>=0.46.2"

RUN pip install --no-cache-dir --target=/install -r requirements.txt
#____Stage 2 : Production________________
FROM python:3.11-slim AS Production
WORKDIR /app

COPY --from=Builder /install /usr/local/lib/python3.11/site-packages
COPY ./app ./app

# Must run as root (before USER directive) to write to site-packages
RUN pip install --upgrade "pip>=26.1" "setuptools>=82.0.1" "wheel>=0.46.2" \
    && pip cache purge

RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid 1001 --no-create-home --shell /bin/false appuser && \
    chown -R appuser:appgroup /app

USER appuser
# ... rest unchanged