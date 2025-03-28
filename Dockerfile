# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies in multiple steps
RUN pip install --no-cache-dir --upgrade pip && \
    # Install base dependencies first
    pip install --no-cache-dir "fastapi==0.109.1" "uvicorn==0.27.0" "python-multipart==0.0.20" \
    "python-jose[cryptography]==3.3.0" "passlib[bcrypt]==1.7.4" "pydantic==2.5.3" "pydantic-settings==2.1.0" \
    "sqlalchemy==2.0.25" "alembic==1.13.1" "asyncpg==0.29.0" "redis==5.0.1" "celery==5.3.6" && \
    # Install authentication dependencies
    pip install --no-cache-dir "fastapi-users[sqlalchemy]==14.0.1" "bcrypt==4.1.2" && \
    # Install document processing dependencies
    pip install --no-cache-dir "langchain-community==0.1.1" "langchain==0.1.1" "openai==1.10.0" \
    "pypdf2==3.0.1" "python-docx==1.0.1" "spacy==3.7.4" && \
    # Install notifications dependencies
    pip install --no-cache-dir "aiosmtplib==3.0.1" "jinja2==3.1.3" "pywebpush==1.14.0" "firebase-admin==6.3.0" && \
    # Install testing dependencies
    pip install --no-cache-dir "pytest==7.4.3" "pytest-asyncio==0.23.4" "pytest-cov==4.1.0" "pytest-mock==3.12.0" \
    "pytest-xdist==3.5.0" "httpx==0.26.0" "aioresponses==0.7.6" "freezegun==1.4.0" "faker==22.6.0" "locust==2.20.1" && \
    # Install security testing dependencies
    pip install --no-cache-dir "safety>=2.3.5" "bandit==1.7.6" && \
    # Install development dependencies
    pip install --no-cache-dir "black==24.1.1" "isort==5.13.2"

# Download spaCy language models
RUN pip install --no-cache-dir \
    https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl \
    https://github.com/explosion/spacy-models/releases/download/es_core_news_sm-3.7.0/es_core_news_sm-3.7.0-py3-none-any.whl \
    https://github.com/explosion/spacy-models/releases/download/fr_core_news_sm-3.7.0/fr_core_news_sm-3.7.0-py3-none-any.whl \
    https://github.com/explosion/spacy-models/releases/download/de_core_news_sm-3.7.0/de_core_news_sm-3.7.0-py3-none-any.whl

# Copy application code and start script
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Make start script executable
RUN chmod +x /app/start.sh

# Run the startup script
CMD ["/app/start.sh"]
