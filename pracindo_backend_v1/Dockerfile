FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Gunicorn dipasang terpisah untuk server production
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install gunicorn

COPY . .

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]

# Healthcheck di image, bukan di compose.
#
# Jangan lewat HTTP: SECURE_SSL_REDIRECT membuat Django menjawab 301 ke
# https untuk request internal, dan urllib menggantung di TLS handshake
# ke port yang bicara HTTP polos.
#
# Yang diperiksa bukan "apakah Django menjawab", melainkan "apakah Django
# bisa menyentuh database" -- Gunicorn yang hidup tanpa DB akan lolos cek
# port dan menjawab 500 untuk semuanya.
HEALTHCHECK --interval=15s --timeout=10s --start-period=60s --retries=5 \
  CMD python -c "import django,os; os.environ.setdefault('DJANGO_SETTINGS_MODULE','pracindo_erp.settings'); django.setup(); from django.db import connection; connection.cursor().execute('SELECT 1')" || exit 1
