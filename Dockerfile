# Multi-stage or lightweight Python 3.12 image for containerized hosting (e.g. Hugging Face Space)
FROM python:3.12-slim

# Avoid buffering and bytecode generation
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=7860 \
    ENVIRONMENT=production \
    ENV=production

# Install system dependencies needed for native build packages if any
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user (Hugging Face Spaces runs as user 1000)
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Install Python requirements
COPY requirements.txt requirements-ai.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-ai.txt

# Copy application code
COPY . .

# Run optional build index if credentials are provided or gracefully skip
RUN python scripts/build_index.py || true

# Ownership
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 7860

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:7860/api/health || exit 1

# Start server on port 7860
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
