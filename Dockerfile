FROM python:3.13-slim AS builder
ENV PIP_NO_CACHE_DIR=1
WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential pkg-config default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*
COPY newsroom/requirements*.txt ./
RUN python -m pip wheel --wheel-dir /wheels -r requirements-container.txt

FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmariadb3 && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 newsroom
WORKDIR /app
COPY --from=builder /wheels /wheels
COPY newsroom/requirements*.txt ./
RUN python -m pip install --no-index --find-links=/wheels \
    -r requirements-container.txt && rm -rf /wheels
COPY --chown=newsroom:newsroom newsroom/ /app/
COPY --chown=newsroom:newsroom docker/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh && mkdir -p /app/staticfiles \
    && chown newsroom:newsroom /app/staticfiles
USER newsroom
EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "4", "--access-logfile", "-", "--error-logfile", "-"]
