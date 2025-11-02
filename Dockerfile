FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY pyproject.toml ./

# Copy source code
COPY src/ ./src/
COPY examples/ ./examples/
COPY .env.example ./
ENV PYTHONPATH=/app/src
RUN pip install --no-cache-dir -e .

# Create directory for timeline data
RUN mkdir -p /data

# Expose the server port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command - runs the HTTP server
CMD ["python", "-m", "where_was_eye.server", "--host", "0.0.0.0", "--port", "8000"]