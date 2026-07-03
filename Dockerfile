# Single image for all five Python services. Each compose service overrides the
# command to run its uvicorn app. Deps only (package=false); src is on PYTHONPATH.
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.7.6 /uv /bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src ./src
# The compliance inventory (RoPA) is read at runtime by the readiness/DPIA gates — without it any
# governed tool that hits the readiness gate (e.g. growth.experiment.create) 500s in-container.
COPY architecture ./architecture
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1

# Default command is overridden per service in docker-compose.yml.
CMD ["python", "-c", "print('override the command in compose')"]
