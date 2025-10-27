# FROM python:3.12-slim

# WORKDIR /app

# # Install uv tool
# COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# # Copy project files
# COPY pyproject.toml .
# COPY uv.lock .

# # Install dependencies using uv
# RUN uv sync --no-dev --no-cache

# # Add uv-installed Python packages to PATH
# ENV PATH="/app/.venv/bin:$PATH"

# # Copy application code
# COPY . .

# EXPOSE 8000

# # Start FastAPI with uvicorn
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]




FROM python:3.12-slim-trixie

WORKDIR /app

# Install system dependencies and Chrome
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg2 \
    chromium \
    chromium-driver \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    xdg-utils \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/* \
    # Install Chrome
    && curl -LO "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb" \
    && apt-get update \
    && apt-get install -y ./google-chrome-stable_current_amd64.deb \
    && rm google-chrome-stable_current_amd64.deb \
    && rm -rf /var/lib/apt/lists/*


# Install uv tool
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy project files
COPY pyproject.toml .
COPY uv.lock .

# Install dependencies using uv
RUN uv sync --no-dev --no-cache

# Add uv-installed Python packages to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY . .

# Set environment variables for Chrome
ENV CHROMIUM_PATH=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]