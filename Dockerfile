# ============================================================
# Stage 1: Builder — instala dependencias con uv
# ============================================================
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Copiar archivos de dependencias primero (cache de capas)
COPY pyproject.toml uv.lock* ./

# Instalar dependencias (sin dev, sin el proyecto en sí)
RUN uv sync --frozen --no-install-project --no-dev

# Copiar el resto del código
COPY . .

# Instalar el proyecto
RUN uv sync --frozen --no-dev --no-install-workspace

# ============================================================
# Stage 2: Runtime — imagen mínima de producción
# ============================================================
FROM python:3.12-slim-bookworm AS runtime

WORKDIR /app

# Dependencias del sistema para psycopg
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 && \
    rm -rf /var/lib/apt/lists/*

# Copiar el virtualenv y el código desde el builder
COPY --from=builder /app /app

# Corregir symlinks de Python (apuntan al Python de uv en el builder)
RUN ln -sf "$(which python3.12)" /app/.venv/bin/python3.12 && \
    ln -sf python3.12 /app/.venv/bin/python3 && \
    ln -sf python3.12 /app/.venv/bin/python

# Poner el venv en el PATH
ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8000

# Comando por defecto (puede sobreescribirse en docker-compose)
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]