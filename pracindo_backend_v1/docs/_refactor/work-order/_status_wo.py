"""
FASE 0 — status sebenarnya work_order, per-endpoint.

READ-ONLY total: hanya membaca URLconf, state migrasi, dan SELECT COUNT.
Tidak ada INSERT/UPDATE/DELETE/CREATE.

Jalankan dari root proyek:
    python docs/_refactor/work-order/_status_wo.py
"""
import os
import re
import sys

import django

_HERE = os.path.abspath(__file__)
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(_HERE))))
sys.path.insert(0, ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pracindo_erp.settings")
django.setup()

from django.db import connection                               # noqa: E402
from django.urls import get_resolver                           # noqa: E402
from django.urls.resolvers import URLResolver                  # noqa: E402


def norm(pattern):
    s = pattern.replace("^", "").replace("$", "")
    s = re.sub(r"\(\?P<([a-zA-Z_]+)>[^)]*\)", r"{\1}", s)
    s = s.replace("\\.", ".").replace("\\", "")
    return ("/" + s.lstrip("/")).replace("{pk}", "{id}")


def routes():
    raw = []

    def walk(res, prefix=""):
        for p in res.url_patterns:
            if isinstance(p, URLResolver):
                walk(p, prefix + str(p.pattern))
            else:
                raw.append((prefix + str(p.pattern), p.callback, p.name))

    walk(get_resolver())

    rows = []
    for pat, cb, name in raw:
        if not pat.startswith("api/"):
            continue
        path = norm(pat)
        if "{format}" in path or "drf_format_suffix" in path:
            continue
        cls = getattr(cb, "cls", None) or getattr(cb, "view_class", None)
        if cls is not None and cls.__name__ == "APIRootView":
            continue
        acts = getattr(cb, "actions", None) or getattr(cb, "initkwargs", {}).get("actions")
        if acts:
            for m, a in acts.items():
                rows.append((m.upper(), path, a, name))
        else:
            for m in ("get", "post", "put", "patch", "delete"):
                if m in cls.__dict__ or any(m in k.__dict__ for k in cls.__mro__[:-3]):
                    rows.append((m.upper(), path, m, name))
    seen, uniq = set(), []
    for r in rows:
        if (r[0], r[1]) in seen:
            continue
        seen.add((r[0], r[1]))
        uniq.append(r)
    return uniq


def main():
    uniq = routes()
    wo = sorted([r for r in uniq if "/work-order/" in r[1]], key=lambda x: (x[1], x[0]))

    print("=" * 74)
    print("A. ROUTE work_order DARI RESOLVER DJANGO (sumber kebenaran)")
    print("=" * 74)
    print(f"total pasangan method+path unik SELURUH api/ : {len(uniq)}")
    print(f"milik work_order                            : {len(wo)}")
    for m, p, a, n in wo:
        print(f"   {m:7s} {p:42s} action={a:15s} url_name={n}")

    print()
    print("=" * 74)
    print("B. STATE MIGRASI vs MODEL")
    print("=" * 74)
    from django.db.migrations.loader import MigrationLoader
    loader = MigrationLoader(connection)
    applied = sorted(k for k in loader.applied_migrations if k[0] == "work_order")
    ondisk = sorted(k for k in loader.disk_migrations if k[0] == "work_order")
    print(f"   migrasi di disk    : {[k[1] for k in ondisk]}")
    print(f"   migrasi ter-apply  : {[k[1] for k in applied]}")

    with connection.cursor() as c:
        c.execute("select table_name from information_schema.tables "
                  "where table_schema='public' and table_name like 'wo_%%' order by 1")
        tables = [r[0] for r in c.fetchall()]
    print(f"   tabel wo_* di DB   : {tables}")

    print()
    print("=" * 74)
    print("C. JUMLAH BARIS (SELECT COUNT saja)")
    print("=" * 74)
    from work_order import models as wm
    for name in ("WorkOrder", "WorkOrderPenugasan", "WorkOrderPesan",
                 "DetailPesananProduksi"):
        M = getattr(wm, name, None)
        if M is None:
            print(f"   {name:24s} model tidak ada")
            continue
        tbl = M._meta.db_table
        if tbl not in tables:
            print(f"   {name:24s} TABEL '{tbl}' TIDAK ADA di DB -> query apa pun 500")
            continue
        print(f"   {name:24s} tabel={tbl:22s} COUNT = {M.objects.count()}")

    print()
    print("=" * 74)
    print("D. profil_staff_id — atribut yang dipakai 3 tempat")
    print("=" * 74)
    from staff_user.models import Profil
    names = {f.name for f in Profil._meta.get_fields()}
    print(f"   'profil_staff_id' ada di Profil? {'profil_staff_id' in names}")
    print(f"   'profil_staff'    ada di Profil? {'profil_staff' in names}")
    print(f"   AUTH_USER_MODEL                 = "
          f"{django.conf.settings.AUTH_USER_MODEL}")
    print(f"   getattr(Profil(), 'profil_staff_id', '<TIDAK ADA>') = "
          f"{getattr(Profil(), 'profil_staff_id', '<TIDAK ADA>')}")
    print(f"   -> maka getattr(request.user,'profil_staff_id',None) SELALU None")


if __name__ == "__main__":
    main()
