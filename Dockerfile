# ===== Stage 1: Builder =====
FROM python:3.11@sha256:9800957d2a88867f853ce6072ae1669e37fa269cc6f76009fa1aef4757f62212 AS builder

WORKDIR /app

# Create a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .

# Upgrade packaging tools and install dependencies
RUN pip install --upgrade \
    "pip>=26.1" \
    "setuptools>=82.0.1" \
    "wheel>=0.46.2"

RUN pip install --no-cache-dir -r requirements.txt


# ===== Stage 2: Production =====
FROM python:3.11-slim@sha256:cdbd05fb6f457ca275ff51ce00d93d865ca0b6a25f5ffb08262d94f6835771e5 AS production

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY ./app ./app

# Fix vulnerable base-image packages in /usr/local/lib (found by Trivy)
# These are separate from /opt/venv — system pip must be called explicitly
RUN /usr/local/bin/python -m pip install --upgrade \
    "pip>=26.1" \
    "setuptools>=82.0.1" \
    "wheel>=0.46.2" \
    "jaraco.context>=6.1.0" \
    && pip cache purge

RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid 1001 --no-create-home --shell /usr/sbin/nologin appuser && \
    chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]