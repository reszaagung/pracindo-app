"""
Inventaris simbol lewat AST — dipakai FASE 1 supaya id node tidak ditebak.
Jalankan: python docs/_scan/graph/_symbols.py
READ-ONLY terhadap kode aplikasi.
"""
import ast
import json
import os

_HERE = os.path.abspath(__file__)
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(_HERE))))
OUT = os.path.join(ROOT, "docs", "_scan", "graph")

APPS = ["core", "staff_user", "master", "dokumen", "inventory", "akunting",
        "keuangan", "warehouse", "produksi", "work_order", "audit",
        "pajak", "sales_order", "logistik"]

# modul yang dipindai per app -> (nama file relatif, kategori)
SCAN = [("views.py", "view"), ("serializers.py", "serializer"),
        ("services.py", "service"), ("models.py", "model"),
        ("permissions.py", "permission"), ("utils.py", "util"),
        ("authentication.py", "auth"), ("posting_rules.py", "rules")]


def parse(path):
    with open(path, encoding="utf-8-sig") as fh:
        return ast.parse(fh.read(), filename=path)


def main():
    out = {}
    for app in APPS:
        for fname, kind in SCAN:
            p = os.path.join(ROOT, app, fname)
            if not os.path.isfile(p) or os.path.getsize(p) == 0:
                continue
            tree = parse(p)
            classes, funcs = [], []
            for n in tree.body:
                if isinstance(n, ast.ClassDef):
                    bases = []
                    for b in n.bases:
                        bases.append(ast.unparse(b))
                    classes.append({"name": n.name, "line": n.lineno, "bases": bases})
                elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    funcs.append({"name": n.name, "line": n.lineno,
                                  "deco": [ast.unparse(d) for d in n.decorator_list]})
            out[f"{app}/{fname}"] = {"kind": kind, "classes": classes, "funcs": funcs}

    # akunting/models adalah paket
    for sub in ("akun", "hutang", "jurnal", "pembelian"):
        p = os.path.join(ROOT, "akunting", "models", f"{sub}.py")
        tree = parse(p)
        out[f"akunting/models/{sub}.py"] = {
            "kind": "model",
            "classes": [{"name": n.name, "line": n.lineno,
                         "bases": [ast.unparse(b) for b in n.bases]}
                        for n in tree.body if isinstance(n, ast.ClassDef)],
            "funcs": [],
        }

    with open(os.path.join(OUT, "_symbols.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)

    for mod, d in out.items():
        cs = ", ".join(c["name"] for c in d["classes"])
        fs = ", ".join(f["name"] for f in d["funcs"] if not f["name"].startswith("__"))
        print(f"--- {mod}  [{d['kind']}]")
        if cs:
            print(f"    class: {cs}")
        if fs:
            print(f"    def  : {fs}")


if __name__ == "__main__":
    main()
