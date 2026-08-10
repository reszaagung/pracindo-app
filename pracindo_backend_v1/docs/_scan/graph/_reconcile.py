"""
FASE 0 — rekonsiliasi jumlah endpoint.

Membandingkan TIGA sumber:
  A. Resolver Django  (sumber kebenaran = kode)
  B. docs/_scan/openapi.yaml   (drf-spectacular)
  C. docs/_scan/api-map.json   (hasil telusur manual fase sebelumnya)

READ-ONLY terhadap kode aplikasi. Hanya membaca URLconf, tidak menyentuh DB.
Jalankan dari root proyek:  python docs/_scan/graph/_reconcile.py
"""
import json
import os
import re
import sys

import django

_HERE = os.path.abspath(__file__)                       # docs/_scan/graph/_reconcile.py
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(_HERE))))
sys.path.insert(0, ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pracindo_erp.settings")
django.setup()

from django.urls import get_resolver                      # noqa: E402
from django.urls.resolvers import URLResolver             # noqa: E402

SCAN = os.path.join(ROOT, "docs", "_scan")
OUT = os.path.join(SCAN, "graph")


def norm(pattern: str) -> str:
    """regex URLconf -> path gaya OpenAPI."""
    s = pattern
    s = s.replace("^", "").replace("$", "")
    s = re.sub(r"\(\?P<([a-zA-Z_]+)>[^)]*\)", r"{\1}", s)
    s = s.replace(r"\.", ".").replace("\\", "")
    s = "/" + s.lstrip("/")
    s = s.replace("{pk}", "{id}")          # drf-spectacular menamainya {id}
    return s


# ---------------------------------------------------------------- A. resolver
def from_resolver():
    raw = []

    def walk(res, prefix=""):
        for p in res.url_patterns:
            if isinstance(p, URLResolver):
                walk(p, prefix + str(p.pattern))
            else:
                raw.append((prefix + str(p.pattern), p.callback, p.name))

    walk(get_resolver())

    rows, dropped = [], {"format_suffix": 0, "api_root": 0, "non_api": 0}
    for pat, cb, urlname in raw:
        if not pat.startswith("api/"):
            dropped["non_api"] += 1
            continue
        path = norm(pat)
        if "{format}" in path or "drf_format_suffix" in path:
            dropped["format_suffix"] += 1
            continue

        cls = getattr(cb, "cls", None) or getattr(cb, "view_class", None)
        view = f"{cls.__module__}.{cls.__name__}" if cls else "?"
        if cls is not None and cls.__name__ == "APIRootView":
            dropped["api_root"] += 1
            continue

        actions = getattr(cb, "actions", None) or getattr(cb, "initkwargs", {}).get("actions")
        if actions:
            for method, action in actions.items():
                rows.append((method.upper(), path, view, action, urlname))
        else:
            for m in ("get", "post", "put", "patch", "delete"):
                if m in cls.__dict__ or any(m in k.__dict__ for k in cls.__mro__[:-3]):
                    rows.append((m.upper(), path, view, m, urlname))

    # dedupe
    seen, uniq = set(), []
    for r in rows:
        if (r[0], r[1]) in seen:
            continue
        seen.add((r[0], r[1]))
        uniq.append(r)
    return uniq, dropped


# ---------------------------------------------------------------- B. openapi
def from_openapi():
    pairs, cur, inside = [], None, False
    with open(os.path.join(SCAN, "openapi.yaml"), encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("paths:"):
                inside = True
                continue
            if inside and line.startswith("components:"):
                break
            if not inside:
                continue
            m = re.match(r"^  (/\S+):", line)
            if m:
                cur = m.group(1)
                continue
            m = re.match(r"^    (get|post|put|patch|delete):", line)
            if m and cur:
                pairs.append((m.group(1).upper(), cur))
    return pairs


# ---------------------------------------------------------------- C. api-map
def from_apimap():
    data = json.load(open(os.path.join(SCAN, "api-map.json"), encoding="utf-8"))
    pairs, entries = [], data["endpoints"]
    for e in entries:
        methods = [m.strip() for m in e["method"].split("|")]
        paths = [p.strip() for p in e["path"].split(",")]
        # bentuk "/a/b/ , /{id}/" -> path kedua relatif terhadap induk
        norm_paths = []
        for p in paths:
            if p.startswith("/api/"):
                norm_paths.append(p)
            else:
                base = norm_paths[0] if norm_paths else paths[0]
                norm_paths.append(base.rstrip("/") + "/" + p.strip("/") + "/")
        for m in methods:
            for p in norm_paths:
                pairs.append((m, p))
    return pairs, len(entries)


def main():
    res, dropped = from_resolver()
    res_set = {(m, p) for m, p, *_ in res}
    api = from_openapi()
    api_set = set(api)
    amp, amp_entries = from_apimap()
    amp_set = set(amp)

    print("=" * 72)
    print("FASE 0 — REKONSILIASI JUMLAH ENDPOINT")
    print("=" * 72)
    print(f"A. Resolver Django      : {len(res_set):3d} pasangan method+path unik")
    print(f"   dibuang: format-suffix={dropped['format_suffix']}, "
          f"APIRootView={dropped['api_root']}, non-api={dropped['non_api']}")
    print(f"B. openapi.yaml         : {len(api_set):3d} pasangan (dari {len(api)} baris)")
    print(f"C. api-map.json         : {len(amp_set):3d} pasangan hasil ekspansi "
          f"(dari {amp_entries} entri)")
    print()

    print("--- ADA DI RESOLVER, TIDAK DI OPENAPI ---")
    for r in sorted(res_set - api_set):
        print("   ", r[0], r[1])
    print("--- ADA DI OPENAPI, TIDAK DI RESOLVER ---")
    for r in sorted(api_set - res_set):
        print("   ", r[0], r[1])
    print()
    print("--- ADA DI RESOLVER, TIDAK DI API-MAP.JSON  (kekurangan api-map) ---")
    miss = sorted(res_set - amp_set)
    for r in miss:
        print("   ", r[0], r[1])
    print(f"    total kurang: {len(miss)}")
    print()
    print("--- ADA DI API-MAP.JSON, TIDAK DI RESOLVER  (salah tulis) ---")
    extra = sorted(amp_set - res_set)
    for r in extra:
        print("   ", r[0], r[1])
    print(f"    total kelebihan: {len(extra)}")

    json.dump(
        {
            "resolver": sorted([{"method": m, "path": p, "view": v, "action": a,
                                 "url_name": n} for m, p, v, a, n in res],
                               key=lambda d: (d["path"], d["method"])),
            "counts": {"resolver": len(res_set), "openapi": len(api_set),
                       "api_map_json_pairs": len(amp_set),
                       "api_map_json_entries": amp_entries},
            "dropped_by_resolver": dropped,
            "missing_from_api_map": [{"method": m, "path": p} for m, p in miss],
            "extra_in_api_map": [{"method": m, "path": p} for m, p in extra],
        },
        open(os.path.join(OUT, "_reconcile.json"), "w", encoding="utf-8"),
        indent=1, ensure_ascii=False,
    )
    print("\nDetail tersimpan di docs/_scan/graph/_reconcile.json")


if __name__ == "__main__":
    main()
