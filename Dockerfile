FROM node:24-bookworm-slim AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend ./
RUN npm run build

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/backend/src
ENV APP_STATIC_DIR=/app/frontend-out
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

WORKDIR /app/backend

COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev

COPY backend/src ./src
COPY --from=frontend-builder /app/frontend/out /app/frontend-out

RUN adduser --disabled-password --gecos "" appuser && \
    mkdir -p /app/backend/data && \
    chown -R appuser /app
USER appuser

EXPOSE 8000

CMD ["uv", "run", "--frozen", "--no-dev", "uvicorn", "project_management_backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
