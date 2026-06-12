FROM python:3.12-slim-bookworm

# System deps: WeasyPrint (Pango/Cairo/gdk-pixbuf) + Vietnamese/CJK fonts.
# (Emoji come from the bundled monochrome Noto Emoji @font-face in
# templates/reports/_fonts.css — the colour-emoji apt font renders as garbled
# specks in WeasyPrint, so it is intentionally NOT installed here.)
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        wget \
        fontconfig \
        shared-mime-info \
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
        libpangoft2-1.0-0 \
        libcairo2 \
        libgdk-pixbuf-2.0-0 \
        libffi8 \
        libjpeg62-turbo \
        fonts-dejavu-core \
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
