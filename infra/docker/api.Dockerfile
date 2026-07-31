# Multi-stage build: the builder stage has compilers and pip caches;
# the runtime stage ships only the installed packages + code.
# Result: smaller image, smaller attack surface, faster pulls.

# --- Stage 1: builder ---------------------------------------------------
FROM python:3.12-slim AS builder

WORKDIR /build

# Install into an isolated venv we can copy wholesale into the runtime image.
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy dependency manifest FIRST, alone. Docker caches layers: as long as
# pyproject.toml is unchanged, this expensive layer is reused even when
# app code changes — turning rebuilds from minutes into seconds.
COPY pyproject.toml .
RUN pip install --no-cache-dir . && pip uninstall -y ai-log-analyzer || true

# --- Stage 2: runtime ---------------------------------------------------
FROM python:3.12-slim AS runtime

# Never run containers as root: a container escape becomes a root escape.
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /srv
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY app ./app
# Bundle Alembic so migrations run inside the container (docker compose exec api
# alembic upgrade head) without copying files in by hand on the target host.
COPY alembic.ini ./alembic.ini
COPY alembic ./alembic

USER appuser
EXPOSE 8000

# Liveness at the container level too (docker/compose healthcheck).
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD python -c "import urllib.request as u; u.urlopen('http://127.0.0.1:8000/api/v1/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
