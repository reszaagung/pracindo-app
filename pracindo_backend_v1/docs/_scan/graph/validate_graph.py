"""
Validator graph.json — FASE 1.

Empat pemeriksaan yang diminta:
  1. tidak ada edge menggantung (source/target harus ada di nodes)
  2. setiap finding_ids ada di 05-findings.md
  3. semua 8 temuan CRITICAL muncul di minimal satu node
  4. jumlah node type=endpoint == angka final FASE 0 (152)

Plus satu pemeriksaan tambahan yang murah dan penting:
  5. setiap edge state=missing menyebut id temuan  (edge missing adalah inti
     nilai graf ini; kalau tidak bisa dilacak ke temuan, ia tidak bisa dipercaya)

Keluar dengan kode 1 kalau ada yang gagal.
Jalankan: python docs/_scan/graph/validate_graph.py
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCAN = os.path.dirname(HERE)
ENDPOINT_TARGET = 152          # putusan FASE 0, lihat graph/00-reconcile.md

fails = []
ok = []


def check(name, passed, detail=""):
    (ok if passed else fails).append((name, detail))
    mark = "PASS" if passed else "FAIL"
    print(f"[{mark}] {name}")
    if detail:
        for line in detail.splitlines():
            print(f"       {line}")


def main():
    graph = json.load(open(os.path.join(HERE, "graph.json"), encoding="utf-8"))
    nodes, edges = graph["nodes"], graph["edges"]
    ids = {n["id"] for n in nodes}

    print(f"graph.json: {len(nodes)} node, {len(edges)} edge\n")

    # --- 1. edge menggantung -------------------------------------------------
    dangling = []
    for e in edges:
        if e["source"] not in ids:
            dangling.append(f"source hilang: {e['source']}  ({e['type']})")
        if e["target"] not in ids:
            dangling.append(f"target hilang: {e['target']}  ({e['type']})")
    check("1. tidak ada edge menggantung",
          not dangling,
          "\n".join(dangling[:20]) + (f"\n... +{len(dangling)-20} lagi"
                                      if len(dangling) > 20 else ""))

    # --- 2. finding_ids dikenal 05-findings.md -------------------------------
    src = open(os.path.join(SCAN, "05-findings.md"), encoding="utf-8").read()
    known = set(re.findall(r"^\|\s*([CHML]\d{1,2})\s*\|", src, re.M))
    used = {f for n in nodes for f in n.get("finding_ids", [])}
    unknown = sorted(used - known)
    check(f"2. finding_ids dikenal 05-findings.md "
          f"({len(known)} temuan terdaftar, {len(used)} dipakai)",
          not unknown,
          "tidak ada di 05-findings.md: " + ", ".join(unknown) if unknown else "")

    # --- 3. seluruh CRITICAL terpetakan -------------------------------------
    crit_block = src.split("## CRITICAL")[1].split("## HIGH")[0]
    crit = set(re.findall(r"^\|\s*(C\d{1,2})\s*\|", crit_block, re.M))
    missing_crit = sorted(crit - used)
    detail = f"CRITICAL di dokumen: {len(crit)} -> {', '.join(sorted(crit))}"
    if missing_crit:
        detail += f"\nTIDAK terpetakan: {', '.join(missing_crit)}"
    else:
        for c in sorted(crit):
            hit = [n["id"] for n in nodes if c in n.get("finding_ids", [])]
            detail += f"\n  {c}: {len(hit)} node -> {', '.join(hit[:3])}"
    check(f"3. semua {len(crit)} temuan CRITICAL muncul di minimal satu node",
          len(crit) == 8 and not missing_crit, detail)

    # --- 4. jumlah endpoint == FASE 0 ---------------------------------------
    n_ep = sum(1 for n in nodes if n["type"] == "endpoint")
    check(f"4. jumlah node type=endpoint == {ENDPOINT_TARGET} (FASE 0)",
          n_ep == ENDPOINT_TARGET,
          f"ditemukan {n_ep}")

    # --- 5. edge missing bisa dilacak ke temuan -----------------------------
    miss = [e for e in edges if e["state"] == "missing"]
    untraceable = [f"{e['source']} -> {e['target']}"
                   for e in miss if not re.match(r"^\[[CHML]\d", e.get("label", ""))]
    check(f"5. seluruh {len(miss)} edge state=missing menyebut id temuan",
          not untraceable, "\n".join(untraceable))

    # --- ringkasan ----------------------------------------------------------
    from collections import Counter
    print("\n--- ringkasan ---")
    print("type  :", dict(Counter(n["type"] for n in nodes)))
    print("status:", dict(Counter(n["status"] for n in nodes)))
    print("risk  :", dict(Counter(n["risk"] for n in nodes if n["risk"])))
    print("edge  :", dict(Counter(e["type"] for e in edges)))
    print("state :", dict(Counter(e["state"] for e in edges)))
    print(f"\ntemuan tanpa node: "
          f"{', '.join(sorted(known - used)) or '(tidak ada)'}")

    print(f"\n{len(ok)} PASS, {len(fails)} FAIL")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
