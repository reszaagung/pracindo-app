"""
FASE 1 — bangun graph/graph.json.

Sumber:
  * graph/endpoints.json      (152 endpoint kanonik, hasil FASE 0)
  * registry Django           (model, FK, M2M)  -- hanya membaca metadata
  * AST seluruh *.py non-migration (view, serializer, service, import, call)
  * docs/_scan/05-findings.md (risk, dipetakan lewat file:baris -> simbol)
  * docs/_scan/api-map.json   (unreachable_views / _serializers)
  * tabel MISSING/VIOLATION di bawah (kurasi manual dari 04-dependencies.md
    dan 05-findings.md -- inilah inti nilai graf ini)

READ-ONLY terhadap kode aplikasi. Menulis hanya ke docs/_scan/graph/.
Jalankan: python docs/_scan/graph/_build_graph.py
"""
import ast
import json
import os
import re
import sys

import django

_HERE = os.path.abspath(__file__)
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(_HERE))))
sys.path.insert(0, ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pracindo_erp.settings")
django.setup()

from django.apps import apps as django_apps  # noqa: E402

SCAN = os.path.join(ROOT, "docs", "_scan")
OUT = os.path.join(SCAN, "graph")

APPS = ["core", "staff_user", "master", "dokumen", "inventory", "akunting",
        "keuangan", "warehouse", "produksi", "work_order", "audit",
        "pajak", "sales_order", "logistik"]

# app -> lapis arsitektur yang dideklarasikan settings.py:75-96
LAPIS = {"core": 1, "staff_user": 1, "master": 2, "dokumen": 2, "inventory": 3,
         "akunting": 4, "keuangan": 4, "pajak": 4, "warehouse": 4,
         "produksi": 4, "sales_order": 4, "logistik": 4, "work_order": 4,
         "audit": 4}

APP_STATUS = {"audit": "dead", "work_order": "dead",
              "sales_order": "stub", "logistik": "stub", "pajak": "stub",
              "dokumen": "stub"}

MODULES = ["views.py", "serializers.py", "services.py", "models.py",
           "permissions.py", "utils.py", "authentication.py",
           "posting_rules.py", "urls.py"]

WRITE_METHODS = {"create", "save", "delete", "update", "bulk_create",
                 "bulk_update", "get_or_create", "update_or_create",
                 "add", "remove", "set", "clear"}
READ_METHODS = {"filter", "get", "all", "exclude", "aggregate", "annotate",
                "count", "exists", "first", "last", "values", "values_list",
                "order_by", "select_for_update", "select_related",
                "prefetch_related", "none", "distinct", "terbuka", "aktif",
                "bisa_diposting", "jatuh_tempo"}

# ---------------------------------------------------------------------------
# 1. INVENTARIS SIMBOL (AST) -- id node tidak ditebak, diambil dari kode
# ---------------------------------------------------------------------------
SYMBOLS = {}   # file relatif -> [ {name, kind, line, end, bases, deco} ]
TREES = {}     # file relatif -> ast.Module


def rel(path):
    return os.path.relpath(path, ROOT).replace("\\", "/")


def load_sources():
    files = []
    for app in APPS:
        for m in MODULES:
            p = os.path.join(ROOT, app, m)
            if os.path.isfile(p) and os.path.getsize(p) > 0:
                files.append(p)
        pkg = os.path.join(ROOT, app, "models")
        if os.path.isdir(pkg):
            for f in sorted(os.listdir(pkg)):
                if f.endswith(".py") and f != "__init__.py":
                    files.append(os.path.join(pkg, f))
    files.append(os.path.join(ROOT, "pracindo_erp", "urls.py"))
    files.append(os.path.join(ROOT, "pracindo_erp", "settings.py"))

    for p in files:
        r = rel(p)
        with open(p, encoding="utf-8-sig") as fh:
            src = fh.read()
        tree = ast.parse(src, filename=r)
        TREES[r] = tree
        syms = []
        for n in tree.body:
            if isinstance(n, ast.ClassDef):
                syms.append({"name": n.name, "kind": "class", "line": n.lineno,
                             "end": n.end_lineno,
                             "bases": [ast.unparse(b) for b in n.bases],
                             "deco": [ast.unparse(d) for d in n.decorator_list],
                             "node": n})
            elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                syms.append({"name": n.name, "kind": "func", "line": n.lineno,
                             "end": n.end_lineno, "bases": [],
                             "deco": [ast.unparse(d) for d in n.decorator_list],
                             "node": n})
        SYMBOLS[r] = syms


def module_id(relpath):
    """core/views.py -> core.views ; akunting/models/akun.py -> akunting.models"""
    p = relpath[:-3] if relpath.endswith(".py") else relpath
    parts = p.split("/")
    if len(parts) >= 3 and parts[1] == "models":
        return f"{parts[0]}.models"
    return ".".join(parts)


def locate(relpath, line):
    """file:baris -> id node yang memuatnya (dipakai memetakan 05-findings.md).

    Rentang simbol dimulai dari baris DEKORATOR, bukan baris `def`, karena
    05-findings.md kerap menunjuk `@transaction.atomic`. Baris di tingkat modul
    (impor, konfigurasi router) tidak berada di simbol mana pun -- itu jatuh ke
    node app, bukan dianggap gagal.
    """
    syms = SYMBOLS.get(relpath)
    if syms:
        for s in syms:
            start = min([s["line"]] + [d.lineno for d in s["node"].decorator_list])
            if start <= line <= s["end"]:
                return f"{module_id(relpath)}:{s['name']}"
    app = relpath.split("/")[0]
    return app if app in nodes else None


# ---------------------------------------------------------------------------
# 2. TABEL KURASI — edge yang SEHARUSNYA ada tapi tidak ada di kode
#    Setiap baris punya rujukan temuan; inilah yang tidak bisa ditemukan AST.
# ---------------------------------------------------------------------------
MISSING = [
    # C6 — invariant SZA rusak: pool bergerak tanpa buku klaim
    ("inventory.services:pakai_dari_pool", "inventory.models:MutasiKlaim",
     "writes", "C6", "pool berkurang tanpa MutasiKlaim -- invariant SZA rusak"),
    ("inventory.services:hasil_ke_pool", "inventory.models:MutasiKlaim",
     "writes", "C6", "pool bertambah tanpa MutasiKlaim -- invariant SZA rusak"),
    ("inventory.services:pakai_dari_pool", "inventory.models:PosisiKlaim",
     "writes", "C6", "posisi kepemilikan tidak pernah disesuaikan"),
    ("inventory.services:hasil_ke_pool", "inventory.models:PosisiKlaim",
     "writes", "C6", "posisi kepemilikan tidak pernah disesuaikan"),
    # M1 — jalur produksi melewati penjaga periode
    ("inventory.services:pakai_dari_pool", "core.services:pastikan_periode_terbuka",
     "calls", "M1", "periode terkunci tidak diperiksa"),
    ("inventory.services:hasil_ke_pool", "core.services:pastikan_periode_terbuka",
     "calls", "M1", "periode terkunci tidak diperiksa"),
    # H4 — opname menggerakkan nilai persediaan tanpa jurnal
    ("inventory.services:sesuaikan_stok", "akunting.services:posting",
     "calls", "H4", "opname mengubah nilai persediaan tanpa jurnal apa pun"),
    # H5 — pembayaran suplier tidak menyentuh buku bank
    ("akunting.services:alokasi_pembayaran", "keuangan.models:MutasiKas",
     "writes", "H5", "kas berkurang di buku besar, tidak di buku bank"),
    ("akunting.services:alokasi_pembayaran", "keuangan.models:RekeningBank",
     "writes", "H5", "saldo rekening tidak pernah dipotong"),
    # C5 — Dr Hutang diposting sebesar nominal penuh termasuk uang muka
    ("akunting.services:alokasi_pembayaran", "akunting.models:Akun",
     "writes", "C5", "akun uang muka suplier belum ada di COA; kelebihan bayar "
                     "mendebet 2100 Hutang Usaha"),
    # M22 — uang muka masuk, tidak pernah dipakai
    ("akunting.services:alokasi_pembayaran", "akunting.models:UangMukaSuplier",
     "reads", "M22", "sisa uang muka tidak pernah dialokasikan ke faktur"),
    # H3 — GRNI menggantung sebesar potongan klaim
    ("akunting.services:terbitkan_faktur", "akunting.models:JurnalUmum",
     "writes", "H3", "jurnal ketiga Dr 2190 GRNI / Cr klaim suplier tidak "
                     "pernah diterbitkan -- GRNI menggantung"),
    # C1 — modul keuangan tanpa penjaga akses
    ("keuangan.views:PengeluaranViewSet", "staff_user.permissions:AksesModul",
     "calls", "C1", "permission_classes tidak diset; jatuh ke IsAuthenticated"),
    # C2 — PUT/PATCH/DELETE pengeluaran tidak menyentuh buku mana pun
    ("keuangan.views:PengeluaranViewSet", "keuangan.models:MutasiKas",
     "writes", "C2", "update/destroy tidak menerbitkan mutasi balik"),
    ("keuangan.views:PengeluaranViewSet", "akunting.models:JurnalUmum",
     "writes", "C2", "update/destroy meninggalkan jurnal yatim"),
    # H1 — work order tanpa penjaga modul
    ("work_order.views:WorkOrderViewSet", "staff_user.permissions:AksesModul",
     "calls", "H1", "hanya IsAuthenticated; tidak ada cek modul/kepemilikan"),
    # H6/H7 — penomoran tidak memakai counter yang sudah benar
    ("master.utils:generate_kode_urut", "core.models:CounterDokumen",
     "reads", "H6", "seharusnya memakai CounterDokumen.berikutnya() "
                    "(select_for_update + kolom numerik)"),
    ("work_order.models:WorkOrder", "core.models:CounterDokumen",
     "reads", "H7", "penomoran leksikografis tanpa lock"),
    # H11 — audit tidak pernah dipanggil
    ("akunting.services:kirim_po", "audit.services:catat",
     "calls", "H11", "transisi status tanpa jejak audit"),
    ("akunting.services:batalkan_po", "audit.services:catat",
     "calls", "H11", "transisi status tanpa jejak audit"),
    ("core.services:tutup_periode", "audit.services:catat",
     "calls", "H11", "penutupan periode tanpa jejak audit"),
    ("core.services:buka_periode", "audit.services:catat",
     "calls", "H11", "pembukaan periode tanpa jejak audit"),
    ("staff_user.services:ubah_role", "audit.services:catat",
     "calls", "H11", "perubahan role tanpa jejak audit"),
    ("warehouse.services:selesaikan_laporan", "audit.services:catat",
     "calls", "H11", "resolusi selisih tanpa jejak audit"),
    # M15 — tidak ada jalur unggah lampiran
    ("akunting.services:lampirkan_dokumen", "dokumen.models:Lampiran",
     "writes", "M15", "satu-satunya penulis Lampiran, tapi tidak ada "
                      "pemanggil dan tidak ada endpoint unggah"),
    # M21 — kurang/lebih kirim tidak pernah terdeteksi
    ("warehouse.services:_periksa_selisih", "warehouse.models:PenerimaanItem",
     "reads", "M21", "selisih_po tidak dipakai; KURANG_KIRIM/LEBIH_KIRIM "
                     "tidak pernah diterbitkan"),
    # H14 — penulisan lintas entitas tanpa cek hak
    ("akunting.views:FakturPembelianViewSet", "staff_user.permissions:AksesModul",
     "calls", "H14", "dari-penerimaan/ tidak memanggil bisa_akses_entitas()"),
]

# import lintas app di TINGKAT MODUL yang menabrak aturan satu arah lapis 4
VIOLATION_IMPORTS = {
    ("keuangan.services", "akunting.services"): "V1",
    ("warehouse.views", "akunting.models"): "V2",
    ("warehouse.serializers", "akunting.models"): "V2",
}

# tulis langsung ke tabel app lain (04-dependencies.md §4)
VIOLATION_WRITES = [
    ("warehouse.services:terima_barang", "akunting.models:PurchaseOrder",
     "M13", "mengubah status PO milik app lain"),
    ("warehouse.services:_simpan_item", "akunting.models:PurchaseOrderItem",
     "M13", "memutakhirkan qty_diterima milik app lain"),
    ("warehouse.services:_buka_kembali_po", "akunting.models:PurchaseOrder",
     "M13", "mengembalikan status PO milik app lain"),
]

# ---------------------------------------------------------------------------
# 3. TEMUAN -> lokasi (verbatim dari 05-findings.md kolom "Lokasi")
# ---------------------------------------------------------------------------
FINDINGS = {
    "C1": ("CRITICAL", ["keuangan/views.py:10"], []),
    "C2": ("CRITICAL", ["keuangan/views.py:10"], ["keuangan.serializers:PengeluaranKasSerializer"]),
    "C3": ("CRITICAL", ["akunting/views.py:348", "akunting/services.py:186"], []),
    "C4": ("CRITICAL", ["keuangan/services.py:46"], []),
    "C5": ("CRITICAL", ["akunting/services.py:233"], []),
    "C6": ("CRITICAL", ["inventory/services.py:264", "inventory/services.py:285"], []),
    "C7": ("CRITICAL", ["keuangan/services.py:29", "keuangan/views.py:30"], []),
    "C8": ("CRITICAL", [], ["pracindo_erp"]),
    "H1": ("HIGH", ["work_order/views.py:14"], []),
    "H2": ("HIGH", ["work_order/views.py:25", "work_order/views.py:51"], []),
    "H3": ("HIGH", ["akunting/services.py:589", "warehouse/services.py:215"], []),
    "H4": ("HIGH", ["inventory/services.py:402"], []),
    "H5": ("HIGH", ["akunting/services.py:186"], []),
    "H6": ("HIGH", ["master/utils.py:9"], []),
    "H7": ("HIGH", ["work_order/models.py:40"], []),
    "H8": ("HIGH", ["work_order/serializers.py:36"], []),
    "H9": ("HIGH", ["warehouse/serializers.py:196"], []),
    "H10": ("HIGH", ["warehouse/serializers.py:189"], []),
    "H11": ("HIGH", [], ["audit", "audit.services:catat",
                         "audit.views:JejakAktivitasViewSet",
                         "audit.models:JejakAktivitas"]),
    "H12": ("HIGH", ["staff_user/views.py:147", "staff_user/serializers.py:27"], []),
    "H13": ("HIGH", ["staff_user/views.py:33", "staff_user/views.py:61"], ["pracindo_erp"]),
    "H14": ("HIGH", ["akunting/views.py:276"], []),
    "H15": ("HIGH", ["akunting/views.py:217", "akunting/views.py:359"], []),
    "H16": ("HIGH", ["akunting/models/hutang.py:203"], []),
    "H17": ("HIGH", ["akunting/services.py:110"], ["akunting.models:JurnalDetail"]),
    "M1": ("MEDIUM", ["inventory/services.py:264", "inventory/services.py:285"], []),
    "M2": ("MEDIUM", ["keuangan/services.py:55"], []),
    "M3": ("MEDIUM", ["inventory/services.py:499", "inventory/services.py:522",
                      "inventory/services.py:540", "inventory/views.py:242"], []),
    "M4": ("MEDIUM", ["produksi/views.py:70"], []),
    "M5": ("MEDIUM", ["inventory/services.py:54", "core/services.py:50"], []),
    "M6": ("MEDIUM", ["inventory/services.py:228", "inventory/services.py:334",
                      "warehouse/services.py:88"], []),
    "M7": ("MEDIUM", ["inventory/services.py:229"], []),
    "M8": ("MEDIUM", ["akunting/views.py:172", "akunting/services.py:58",
                      "akunting/services.py:302", "akunting/services.py:443",
                      "akunting/services.py:503", "warehouse/services.py:307",
                      "core/services.py:72"], []),
    "M9": ("MEDIUM", ["keuangan/models.py:51", "keuangan/services.py:22"], []),
    "M10": ("MEDIUM", ["keuangan/models.py:107"], []),
    "M11": ("MEDIUM", ["keuangan/models.py:181"], []),
    "M12": ("MEDIUM", ["master/views.py:19", "core/views.py:56"], []),
    "M13": ("MEDIUM", ["warehouse/services.py:88", "warehouse/views.py:19",
                       "warehouse/serializers.py:19"], []),
    "M14": ("MEDIUM", ["keuangan/services.py:7"], ["keuangan.services:catat_pengeluaran"]),
    "M15": ("MEDIUM", ["akunting/services.py:406"], ["dokumen.models:Lampiran"]),
    "M16": ("MEDIUM", [], ["inventory.models:NilaiEkuivalen", "produksi.models:Resep",
                           "master.models:Satuan", "master.models:Kategori",
                           "master.models:Pelanggan"]),
    "M17": ("MEDIUM", [], ["pracindo_erp"]),
    "M18": ("MEDIUM", [], []),   # 8 endpoint, dipetakan lewat flag di endpoints.json
    "M19": ("MEDIUM", ["akunting/models/pembelian.py:158"], []),
    "M20": ("MEDIUM", ["work_order/models.py:56"], []),
    "M21": ("MEDIUM", ["warehouse/services.py:231"], []),
    "M22": ("MEDIUM", ["akunting/models/hutang.py:274", "akunting/services.py:228"], []),
    "M23": ("MEDIUM", ["warehouse/services.py:403"], []),
    "M24": ("MEDIUM", ["core/services.py:79"], []),
    "L1": ("LOW", [], ["pracindo_erp"]),
    "L2": ("LOW", ["produksi/serializers.py:11"], []),
    "L3": ("LOW", ["produksi/views.py:23"], []),
    "L4": ("LOW", ["keuangan/views.py:49"], []),
    "L5": ("LOW", ["keuangan/views.py:35"], []),
    "L6": ("LOW", ["master/urls.py:4"], ["master"]),
    "L7": ("LOW", ["core/views.py:23", "staff_user/views.py:26",
                   "inventory/views.py:39", "warehouse/views.py:33",
                   "akunting/views.py:35", "produksi/views.py:11"], []),
    "L8": ("LOW", [], ["pracindo_erp"]),
    "L9": ("LOW", [], ["pracindo_erp"]),
    "L10": ("LOW", ["akunting/models/pembelian.py:202", "warehouse/models.py:72"], []),
    "L11": ("LOW", ["master/models.py:151", "keuangan/models.py:186",
                    "akunting/models/pembelian.py:220", "warehouse/models.py:198"], []),
    "L12": ("LOW", ["core/models.py:137"], []),
    "L13": ("LOW", ["produksi/models.py:49", "staff_user/permissions.py:167",
                    "staff_user/permissions.py:182", "staff_user/serializers.py:15",
                    "akunting/models/pembelian.py:134", "akunting/models/akun.py:89",
                    "keuangan/models.py:128", "inventory/services.py:365",
                    "inventory/services.py:559"], []),
    "L14": ("LOW", ["staff_user/authentication.py:46"], []),
    "L15": ("LOW", [], ["pracindo_erp"]),
}

RISK_RANK = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}

# ---------------------------------------------------------------------------
# 4. BANGUN NODE
# ---------------------------------------------------------------------------
nodes = {}
edges = []


def add_node(nid, **kw):
    if nid in nodes:
        return nodes[nid]
    kw.setdefault("risk", None)
    kw.setdefault("finding_ids", [])
    kw.setdefault("meta", {})
    kw["id"] = nid
    nodes[nid] = kw
    return kw


def add_edge(src, dst, etype, file=None, line=0, state="present", label=None):
    e = {"source": src, "target": dst, "type": etype, "file": file,
         "line": line, "state": state}
    if label:
        e["label"] = label
    edges.append(e)


def build_apps():
    installed = {a.label for a in django_apps.get_app_configs()}
    for app in APPS:
        add_node(app, type="app", app=app, layer=None,
                 file=f"{app}/apps.py", line=1, label=app,
                 status=APP_STATUS.get(app, "live"),
                 meta={"lapis": LAPIS[app], "installed": app in installed})
    add_node("pracindo_erp", type="app", app="pracindo_erp", layer=None,
             file="pracindo_erp/settings.py", line=1, label="pracindo_erp (proyek)",
             status="live", meta={"lapis": 0, "installed": True})


def build_models():
    for m in django_apps.get_models():
        app = m._meta.app_label
        if app not in APPS:
            continue
        mod = m.__module__
        f = mod.replace(".", "/") + ".py"
        if not os.path.isfile(os.path.join(ROOT, f)):
            f = f"{app}/models.py"
        line = 0
        for s in SYMBOLS.get(f, []):
            if s["name"] == m.__name__:
                line = s["line"]
        nid = f"{app}.models:{m.__name__}"
        add_node(nid, type="model", app=app, layer="data", file=f, line=line,
                 label=m.__name__, status=APP_STATUS.get(app, "live"),
                 meta={"table": m._meta.db_table,
                       "abstract": False,
                       "fields": len(m._meta.local_fields)})
    # audit tidak terpasang -> ambil lewat AST
    for s in SYMBOLS.get("audit/models.py", []):
        if s["kind"] == "class" and any("Model" in b for b in s["bases"]):
            add_node(f"audit.models:{s['name']}", type="model", app="audit",
                     layer="data", file="audit/models.py", line=s["line"],
                     label=s["name"], status="dead",
                     meta={"table": "audit_jejak_aktivitas",
                           "note": "app tidak di INSTALLED_APPS; tabel tidak "
                                   "pernah dibuat"})
    # basis abstrak yang dirujuk temuan M11
    for name in ("TimeStampedModel", "DiauditModel"):
        for s in SYMBOLS.get("core/models.py", []):
            if s["name"] == name:
                add_node(f"core.models:{name}", type="model", app="core",
                         layer="data", file="core/models.py", line=s["line"],
                         label=name, status="live",
                         meta={"abstract": True})


def build_fk_edges():
    for m in django_apps.get_models():
        app = m._meta.app_label
        if app not in APPS:
            continue
        src = f"{app}.models:{m.__name__}"
        for f in m._meta.local_fields:
            if f.related_model is None:
                continue
            tm = f.related_model
            if tm._meta.app_label not in APPS:
                continue
            dst = f"{tm._meta.app_label}.models:{tm.__name__}"
            if dst not in nodes:
                continue
            add_edge(src, dst, "fk", file=nodes[src]["file"],
                     line=nodes[src]["line"],
                     label=f"{f.name} ({f.remote_field.on_delete.__name__})")
        for f in m._meta.local_many_to_many:
            tm = f.related_model
            if tm._meta.app_label not in APPS:
                continue
            dst = f"{tm._meta.app_label}.models:{tm.__name__}"
            if dst in nodes:
                add_edge(src, dst, "m2m", file=nodes[src]["file"],
                         line=nodes[src]["line"], label=f.name)


def build_symbol_nodes():
    unreachable = set()
    amp = json.load(open(os.path.join(SCAN, "api-map.json"), encoding="utf-8"))
    for u in amp["unreachable_views"]:
        unreachable.add(u["view"].rsplit(".", 1)[-1])
    for u in amp["unreachable_serializers"]:
        unreachable.add(u["serializer"].split(" ")[0].rsplit(".", 1)[-1])

    kind_of = {"views.py": ("view", "api"), "serializers.py": ("serializer", "api"),
               "services.py": ("service", "domain"), "utils.py": ("service", "domain"),
               "permissions.py": ("service", "domain"),
               "authentication.py": ("service", "domain"),
               "posting_rules.py": ("service", "domain")}

    for relpath, syms in SYMBOLS.items():
        base = relpath.split("/")[-1]
        if base not in kind_of:
            continue
        app = relpath.split("/")[0]
        if app not in APPS:
            continue
        ntype, layer = kind_of[base]
        for s in syms:
            if s["name"].startswith("__"):
                continue
            if base == "services.py" or base in ("utils.py",):
                if s["kind"] != "func":
                    continue
            nid = f"{module_id(relpath)}:{s['name']}"
            status = APP_STATUS.get(app, "live")
            if s["name"] in unreachable:
                status = "unreachable"
            meta = {}
            if s["deco"]:
                meta["decorators"] = s["deco"]
                meta["atomic"] = any("atomic" in d for d in s["deco"])
            if s["bases"]:
                meta["bases"] = s["bases"]
            add_node(nid, type=ntype, app=app, layer=layer, file=relpath,
                     line=s["line"], label=s["name"], status=status, meta=meta)


def build_db_trigger():
    p = "akunting/migrations/0004_trigger_jurnal_seimbang.py"
    line = 0
    with open(os.path.join(ROOT, p), encoding="utf-8-sig") as fh:
        for i, l in enumerate(fh, 1):
            if "CREATE CONSTRAINT TRIGGER" in l.upper():
                line = i
                break
    add_node("akunting.migrations.0004:trg_jurnal_seimbang", type="db_trigger",
             app="akunting", layer="data", file=p, line=line,
             label="trg_jurnal_seimbang", status="live",
             meta={"deferrable": True,
                   "note": "CONSTRAINT TRIGGER DEFERRABLE -- penjaga keseimbangan "
                           "jurnal yang tidak bisa dilewati bulk_create/shell"})
    for t in ("akunting.models:JurnalUmum", "akunting.models:JurnalDetail"):
        if t in nodes:
            add_edge("akunting.migrations.0004:trg_jurnal_seimbang", t,
                     "listens", file=p, line=line, label="AFTER INSERT/UPDATE")


def build_endpoints():
    eps = json.load(open(os.path.join(OUT, "endpoints.json"), encoding="utf-8"))
    for e in eps:
        nid = f"endpoint:{e['method']} {e['path']}"
        app = e["app"]
        view_cls = e["view"].rsplit(".", 1)[-1]
        view_mod = e["view"].rsplit(".", 1)[0]
        perm = e["permission"]
        add_node(nid, type="endpoint", app=app, layer="api",
                 file=f"{app}/urls.py" if app in APPS else "pracindo_erp/urls.py",
                 line=0, label=f"{e['method']} {e['path']}",
                 status=e["status"],
                 meta={"methods": [e["method"]], "permission": perm,
                       "atomic": e["atomic"], "view": e["view"],
                       "action": e["action"], "write": e["write"],
                       "url_name": e["url_name"],
                       "multi_table_no_atomic": e["multi_table_no_atomic"],
                       "always_400": e["always_400"]})
        vid = f"{view_mod}:{view_cls}"
        if vid in nodes:
            add_edge(nid, vid, "routes_to",
                     file=nodes[vid]["file"], line=nodes[vid]["line"],
                     label=e["action"])
        else:
            # view pihak ketiga (drf-spectacular) -- tidak ada node simbolnya,
            # disambungkan ke node app supaya tidak ada endpoint yatim
            add_edge(nid, app if app in nodes else "pracindo_erp", "routes_to",
                     file=f"{app}/urls.py" if app in APPS else "pracindo_erp/urls.py",
                     line=0, label=f"{view_cls} (view pihak ketiga)")


# ---------------------------------------------------------------------------
# 5. EDGE DARI AST — serializes / calls / reads / writes / imports
# ---------------------------------------------------------------------------
def name_index():
    """nama simbol -> daftar id node (untuk resolusi panggilan & model)."""
    idx = {}
    for nid, n in nodes.items():
        if n["type"] in ("model", "service", "serializer", "view"):
            idx.setdefault(n["label"], []).append(nid)
    return idx


def resolve(name, app, idx, want=None):
    cands = idx.get(name, [])
    if want:
        cands = [c for c in cands if nodes[c]["type"] in want]
    if not cands:
        return None
    same = [c for c in cands if nodes[c]["app"] == app]
    return (same or cands)[0]


def build_ast_edges():
    idx = name_index()

    for relpath, tree in TREES.items():
        app = relpath.split("/")[0]
        if app not in APPS:
            continue
        mod = module_id(relpath)
        base = relpath.split("/")[-1]

        # --- imports lintas app ---
        for n in ast.walk(tree):
            if isinstance(n, ast.ImportFrom) and n.module:
                target_app = n.module.split(".")[0]
                if target_app not in APPS or target_app == app:
                    continue
                tmod = ".".join(n.module.split(".")[:2])
                key = (mod, tmod)
                state = "violation" if key in VIOLATION_IMPORTS else "present"
                if target_app in nodes and app in nodes:
                    add_edge(app, target_app, "imports", file=relpath,
                             line=n.lineno, state=state,
                             label=f"{mod} -> {n.module}"
                                   + (f" [{VIOLATION_IMPORTS[key]}]"
                                      if key in VIOLATION_IMPORTS else ""))

        # --- per simbol: calls / reads / writes / serializes ---
        for s in SYMBOLS.get(relpath, []):
            sid = f"{mod}:{s['name']}"
            if sid not in nodes:
                continue
            for n in ast.walk(s["node"]):
                # Model.objects.<method>  ->  reads/writes
                if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Attribute):
                    if n.value.attr == "objects" and isinstance(n.value.value, ast.Name):
                        mname = n.value.value.id
                        mid = resolve(mname, app, idx, want=("model",))
                        if mid:
                            meth = n.attr
                            et = ("writes" if meth in WRITE_METHODS
                                  else "reads" if meth in READ_METHODS else None)
                            if et:
                                add_edge(sid, mid, et, file=relpath,
                                         line=n.lineno, label=f".objects.{meth}()")
                # panggilan fungsi
                if isinstance(n, ast.Call):
                    fn = n.func
                    cname = None
                    if isinstance(fn, ast.Name):
                        cname = fn.id
                    elif isinstance(fn, ast.Attribute):
                        cname = fn.attr
                    if not cname:
                        continue
                    # serializer?
                    if cname.endswith("Serializer"):
                        tid = resolve(cname, app, idx, want=("serializer",))
                        if tid and tid != sid:
                            add_edge(sid, tid, "serializes", file=relpath,
                                     line=n.lineno)
                        continue
                    tid = resolve(cname, app, idx, want=("service",))
                    if tid and tid != sid:
                        add_edge(sid, tid, "calls", file=relpath, line=n.lineno)
                        continue
                    # Model(...) langsung -> writes
                    tid = resolve(cname, app, idx, want=("model",))
                    if tid and cname[0].isupper():
                        add_edge(sid, tid, "writes", file=relpath, line=n.lineno,
                                 label="konstruksi instance")

            # serializer_class = X  (atribut kelas view)
            if base == "views.py" and s["kind"] == "class":
                for b in s["node"].body:
                    if isinstance(b, ast.Assign):
                        for t in b.targets:
                            if isinstance(t, ast.Name) and t.id in (
                                    "serializer_class", "queryset"):
                                txt = ast.unparse(b.value)
                                m = re.match(r"([A-Za-z_]\w*)", txt)
                                if not m:
                                    continue
                                nm = m.group(1)
                                if t.id == "serializer_class":
                                    tid = resolve(nm, app, idx, want=("serializer",))
                                    if tid:
                                        add_edge(sid, tid, "serializes",
                                                 file=relpath, line=b.lineno,
                                                 label="serializer_class")
                                else:
                                    tid = resolve(nm, app, idx, want=("model",))
                                    if tid:
                                        add_edge(sid, tid, "reads", file=relpath,
                                                 line=b.lineno, label="queryset")

            # serializer -> model  (class Meta: model = X)
            if base == "serializers.py" and s["kind"] == "class":
                for b in ast.walk(s["node"]):
                    if isinstance(b, ast.Assign):
                        for t in b.targets:
                            if isinstance(t, ast.Name) and t.id == "model":
                                nm = ast.unparse(b.value).split(".")[-1]
                                tid = resolve(nm, app, idx, want=("model",))
                                if tid:
                                    add_edge(sid, tid, "serializes", file=relpath,
                                             line=b.lineno, label="Meta.model")

    # Catatan: TIDAK ada edge "containment" app->simbol. Skema edge tidak punya
    # tipe itu, dan memaksanya jadi "imports" akan membuat 415 edge palsu yang
    # mengaburkan import sungguhan. Viewer mengelompokkan lewat field node.app.


def build_curated():
    for src, dst, et, fid, label in MISSING:
        if src not in nodes:
            print(f"  ! MISSING source tidak ada: {src}")
            continue
        if dst not in nodes:
            print(f"  ! MISSING target tidak ada: {dst}")
            continue
        add_edge(src, dst, et, file=nodes[src]["file"], line=nodes[src]["line"],
                 state="missing", label=f"[{fid}] {label}")
    for src, dst, fid, label in VIOLATION_WRITES:
        if src in nodes and dst in nodes:
            add_edge(src, dst, "writes", file=nodes[src]["file"],
                     line=nodes[src]["line"], state="violation",
                     label=f"[{fid}] {label}")


def apply_findings():
    unresolved = []
    for fid, (risk, locs, extra) in FINDINGS.items():
        targets = []
        for loc in locs:
            f, _, ln = loc.rpartition(":")
            nid = locate(f, int(ln))
            if nid and nid in nodes:
                targets.append(nid)
            else:
                unresolved.append((fid, loc, nid))
        targets.extend([e for e in extra if e in nodes])
        for t in set(targets):
            n = nodes[t]
            if fid not in n["finding_ids"]:
                n["finding_ids"].append(fid)
            if n["risk"] is None or RISK_RANK[risk] > RISK_RANK[n["risk"]]:
                n["risk"] = risk
    # M18 — 8 endpoint tanpa paginasi
    for nid, n in nodes.items():
        if n["type"] == "endpoint" and n["meta"].get("action") in (
                "menunggu", "outstanding", "jatuh_tempo", "aging", "terbuka",
                "mading", "staff") and n["meta"]["methods"] == ["GET"]:
            n["finding_ids"].append("M18")
            if n["risk"] is None:
                n["risk"] = "MEDIUM"
    return unresolved


def main():
    load_sources()
    build_apps()
    build_models()
    build_symbol_nodes()
    build_db_trigger()
    build_endpoints()
    build_fk_edges()
    build_ast_edges()
    build_curated()
    unresolved = apply_findings()

    # dedupe edge
    seen, uniq = set(), []
    for e in edges:
        k = (e["source"], e["target"], e["type"], e["state"], e.get("label"), e["line"])
        if k in seen:
            continue
        seen.add(k)
        uniq.append(e)

    graph = {"nodes": list(nodes.values()), "edges": uniq}
    with open(os.path.join(OUT, "graph.json"), "w", encoding="utf-8") as fh:
        json.dump(graph, fh, indent=1, ensure_ascii=False)

    from collections import Counter
    print(f"node  : {len(graph['nodes'])}  {dict(Counter(n['type'] for n in graph['nodes']))}")
    print(f"edge  : {len(uniq)}  {dict(Counter(e['type'] for e in uniq))}")
    print(f"state : {dict(Counter(e['state'] for e in uniq))}")
    print(f"status: {dict(Counter(n['status'] for n in graph['nodes']))}")
    print(f"risk  : {dict(Counter(n['risk'] for n in graph['nodes'] if n['risk']))}")
    if unresolved:
        print(f"\nLOKASI TEMUAN TIDAK TERESOLUSI ({len(unresolved)}):")
        for fid, loc, got in unresolved:
            print(f"   {fid:4s} {loc:45s} -> {got}")


if __name__ == "__main__":
    main()
