FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set working directory
WORKDIR /app

# Install system dependencies in one layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python build dependencies first
RUN pip install --upgrade pip setuptools wheel cython && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code (copy only what's needed)
COPY . .

# Create necessary directories with proper permissions
RUN mkdir -p data models knowledge_base logs && \
    chmod -R 755 /app

# Expose ports
# 8000 for FastAPI backend
# 8501 for Streamlit frontend
EXPOSE 8000 8501

# Health check (only for backend)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command (can be overridden in docker-compose)
CMD ["python", "-m", "uvicorn", "unified_forecaster_app:app", "--host", "0.0.0.0", "--port", "8000"]

