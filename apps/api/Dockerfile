FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for headless browser
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    libgtk-3-0 \
    libasound2 \
    libx11-xcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxi6 \
    libxtst6 \
    libnss3 \
    libcups2 \
    libxss1 \
    libxrandr2 \
    libgconf-2-4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libpangocairo-1.0-0 \
    libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

COPY apps/api/pyproject.toml apps/api/README.md /app/
RUN pip install --no-cache-dir .

COPY apps/api/app /app/app
COPY tests/fixtures /app/tests/fixtures
COPY reports /app/reports

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

