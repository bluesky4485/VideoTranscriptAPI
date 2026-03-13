FROM python:3.11-slim

# ============================================================
# 1. System dependencies: ffmpeg, curl, unzip
# ============================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# ============================================================
# 2. BBDown: download Linux build from GitHub Release
#    BBDown linux-x64 is .NET AOT build, no runtime needed
# ============================================================
RUN curl -L -o /tmp/BBDown.zip \
    https://github.com/nilaoda/BBDown/releases/latest/download/BBDown_linux-x64.zip \
    && mkdir -p /app/BBDown \
    && unzip /tmp/BBDown.zip -d /app/BBDown/ \
    && chmod +x /app/BBDown/BBDown \
    && rm /tmp/BBDown.zip

# ============================================================
# 3. Python package manager: uv
# ============================================================
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# ============================================================
# 4. Python dependencies (cached layer - before source copy)
# ============================================================
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# ============================================================
# 5. Application source code
# ============================================================
COPY src/ ./src/
COPY main.py ./

# ============================================================
# 6. Create runtime directories (overridden by bind mount)
# ============================================================
RUN mkdir -p data/cache data/temp data/workspace data/logs config

# ============================================================
# 7. Runtime configuration
# ============================================================
EXPOSE 8000

ENTRYPOINT ["uv", "run", "python", "main.py", "--start"]
