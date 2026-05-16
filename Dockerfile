# Stage 1: dependency layer 
FROM python:3.12-slim AS deps

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock ./

# Install only production dependencies, no dev extras
RUN uv sync --frozen --no-dev

# Stage 2: runtime image
FROM python:3.12-slim AS runtime

# Copy uv and the pre-built venv from the deps stage
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY --from=deps /app/.venv /app/.venv

WORKDIR /app

# Copy application source
COPY src/   ./src/
COPY docs/  ./docs/
COPY main.py ./

# Activate the venv by putting it first on PATH
ENV PATH="/app/.venv/bin:$PATH"

# AWS Bedrock config — override at ECS task level via environment variables
# or SSM Parameter Store (see infra/iam_policies.py for required permissions)
ENV BEDROCK_REGION="us-east-1"
ENV DOCS_DIR="docs"
ENV FAISS_INDEX_PATH=".cache/faiss_index"
ENV CONFIDENCE_THRESHOLD="0.30"
ENV TOP_K="5"

# Port exposed by uvicorn (must match ALB target group)
EXPOSE 8080

# Health check — ALB uses this to determine task readiness
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"

CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8080", "--log-level", "info"]
