FROM python:3.12-slim

WORKDIR /app

# System deps for Playwright / BeautifulSoup (your scraper likely needs these)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
