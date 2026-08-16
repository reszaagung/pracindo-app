#!/bin/sh
# set -e WAJIB: tanpa itu, migrate yang gagal dilewati diam-diam dan
# Gunicorn tetap start di atas skema yang salah. Sistem yang seluruh
# nilainya bergantung pada satu persamaan akuntansi tidak boleh melayani
# request di atas tabel yang belum ada.
set -e

echo "==> Menunggu database"
python - <<'PY'
import os, sys, time, psycopg2
for i in range(30):
    try:
        psycopg2.connect(
            dbname=os.environ["DB_NAME"], user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            host=os.environ.get("DB_HOST", "db"),
            port=os.environ.get("DB_PORT", "5432"), connect_timeout=3,
        ).close()
        print("    siap"); sys.exit(0)
    except Exception as e:
        print(f"    {i+1}/30: {e}"); time.sleep(2)
sys.exit("database tidak pernah siap")
PY

echo "==> Migrasi"
python manage.py migrate --noinput

echo "==> Collectstatic"
python manage.py collectstatic --noinput

echo "==> Gunicorn"
exec gunicorn pracindo_erp.wsgi:application \
     --bind 0.0.0.0:8000 --workers 3 --timeout 120 --preload \
     --access-logfile - --error-logfile -
