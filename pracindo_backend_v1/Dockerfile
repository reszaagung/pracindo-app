FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libglib2.0-0 \
    libcairo2 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

    
COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install gunicorn

COPY . .

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]

HEALTHCHECK --interval=15s --timeout=10s --start-period=60s --retries=5 \
  CMD python -c "import django,os; os.environ.setdefault('DJANGO_SETTINGS_MODULE','pracindo_erp.settings'); django.setup(); from django.db import connection; connection.cursor().execute('SELECT 1')" || exit 1
