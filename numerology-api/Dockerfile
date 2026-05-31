FROM python:3.12-slim-bookworm

# System deps: wkhtmltopdf + Vietnamese/CJK fonts
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        fontconfig \
        libxrender1 \
        libjpeg62-turbo \
        libxtst6 \
        xfonts-75dpi \
        xfonts-base \
        xz-utils \
        wget \
        wkhtmltopdf \
        fonts-noto-cjk \
        fonts-arphic-ukai \
        fonts-arphic-uming \
        fonts-unfonts-core \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install Python deps first (layer caching)
COPY pyproject.toml ./
RUN pip install --upgrade pip && pip install .

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
