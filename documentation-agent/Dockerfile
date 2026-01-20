# Natterbox Documentation Agent
# Docker container for running the documentation automation agent

FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    jq \
    zip \
    unzip \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

# Create workspace directories
RUN mkdir -p /workspace /workspace/output /app

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY agent.py .
COPY README.md .

# Create a non-root user for security
RUN useradd -m -s /bin/bash agent && \
    chown -R agent:agent /workspace /app

USER agent

# Set working directory to workspace
WORKDIR /workspace

# Default command - interactive mode
ENTRYPOINT ["python", "/app/agent.py"]
CMD ["--interactive"]
