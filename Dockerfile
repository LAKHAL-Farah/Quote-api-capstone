# ===== Stage 1: Builder =====
FROM python:3.11 AS builder

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
FROM python:3.11-slim AS production

WORKDIR /app

# Copy the virtual environment from the builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application source
COPY ./app ./app

# Upgrade packaging tools and clear pip cache
RUN pip install --upgrade \
    "pip>=26.1" \
    "setuptools>=82.0.1" \
    "wheel>=0.46.2" \
    && pip cache purge

# Create non-root user
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid 1001 --no-create-home --shell /usr/sbin/nologin appuser && \
    chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]