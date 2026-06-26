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
COPY --from=Builder /usr/local/lib/python3.11/site-packages/setuptools \
     /usr/local/lib/python3.11/site-packages/setuptools
COPY --from=Builder /usr/local/lib/python3.11/site-packages/setuptools-82.0.1.dist-info \
     /usr/local/lib/python3.11/site-packages/setuptools-82.0.1.dist-info
COPY --from=Builder /usr/local/lib/python3.11/site-packages/wheel \
     /usr/local/lib/python3.11/site-packages/wheel
COPY --from=Builder /usr/local/lib/python3.11/site-packages/wheel-0.46.3.dist-info \
     /usr/local/lib/python3.11/site-packages/wheel-0.46.3.dist-info
COPY ./app ./app


RUN pip install --upgrade "pip>=26.1" "setuptools>=82.0.1" "wheel>=0.46.2" \
    && pip cache purge

RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid 1001 --no-create-home --shell /bin/false appuser && \
    chown -R appuser:appgroup /app

USER appuser

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0" ,"--port", "8000"]