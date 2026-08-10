"""
Generator diagram Mermaid untuk satu app Django — AS-IS, dari kode.

READ-ONLY TOTAL:
  - hanya introspeksi model (_meta), URLconf, dan AST berkas .py
  - TIDAK menyentuh database sama sekali (tidak ada koneksi, tidak ada query)
  - satu-satunya penulisan: berkas .mmd di direktori output

Letakkan di  docs/_refactor/work-order/_gen_mermaid.py
Jalankan dari root proyek:

    python docs/_refactor/work-order/_gen_mermaid.py
    python docs/_refactor/work-order/_gen_mermaid.py --app produksi
    python docs/_refactor/work-order/_gen_mermaid.py --settings config.settings

Keluaran (di direktori skrip ini):
    01-asis-er.mmd      erDiagram seluruh model + FK keluar ke app lain
    01-asis-state.mmd   stateDiagram-v2 siklus hidup + penegakan aturan
    01-asis-flow.mmd    flowchart URL -> View -> Serializer -> Model

Prinsip: yang tidak terverifikasi ditulis UNKNOWN, tidak ditebak.
"""

import argparse
import ast
import inspect
import os
import re
import sys
from collections import defaultdict

DEFAULT_APP = "work_order"

# Nama field yang menandai selesainya siklus hidup, dan field aturannya.
# Ubah di sini kalau app lain memakai nama berbeda.
STATE_FIELD = "selesai"
RULE_FIELD = "aturan_penyelesaian"


# --------------------------------------------------------------------------
# Bootstrap Django
# --------------------------------------------------------------------------

def deteksi_settings():
    """Cari DJANGO_SETTINGS_MODULE dari env, lalu dari manage.py."""
    if os.environ.get("DJANGO_SETTINGS_MODULE"):
        return os.environ["DJANGO_SETTINGS_MODULE"]
    manage = os.path.join(os.getcwd(), "manage.py")
    if os.path.exists(manage):
        with open(manage, encoding="utf-8") as f:
            cocok = re.search(
                r"""DJANGO_SETTINGS_MODULE["']\s*,\s*["']([^"']+)""", f.read()
            )
            if cocok:
                return cocok.group(1)
    return None


def setup_django(settings_module):
    sys.path.insert(0, os.getcwd())
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)
    import django

    django.setup()


# --------------------------------------------------------------------------
# Utilitas Mermaid
# --------------------------------------------------------------------------

def id_aman(teks):
    """ID node mermaid: alfanumerik dan underscore saja."""
    return re.sub(r"\W", "_", str(teks)) or "kosong"


def entitas(model):
    """Nama entitas erDiagram: UPPER_SNAKE dari nama tabel."""
    return re.sub(r"\W", "_", model._meta.db_table).upper()


def label_aman(teks):
    """Label mermaid dalam tanda kutip: buang karakter yang memutus parser."""
    teks = str(teks).replace('"', "'").replace("\n", " ")
    return re.sub(r"[\[\]{}()<>|]", "", teks).strip()


def komentar(bagian):
    """Rakit komentar field erDiagram, dibatasi panjangnya."""
    isi = ", ".join(b for b in bagian if b)
    isi = label_aman(isi)
    return isi[:70] + ("..." if len(isi) > 70 else "")


# --------------------------------------------------------------------------
# 1. erDiagram
# --------------------------------------------------------------------------

def bangun_er(models, nama_app):
    baris = ["erDiagram"]
    relasi = []
    dikenal = {m._meta.label: m for m in models}

    for model in models:
        for field in model._meta.get_fields():
            if not field.is_relation or not getattr(field, "concrete", False):
                continue
            target = field.related_model
            if target is None:
                continue

            luar = target._meta.label not in dikenal
            rel_name = getattr(field.remote_field, "related_name", None) or "UNKNOWN related_name"
            if luar:
                rel_name += f" [luar: {target._meta.app_label}]"

            if field.many_to_many:
                garis = "}o--o{"
            elif field.one_to_one:
                garis = "||--||"
            elif getattr(field, "null", False):
                garis = "|o--o{"
            else:
                garis = "||--o{"

            relasi.append(
                f"    {entitas(target)} {garis} {entitas(model)} : \"{label_aman(rel_name)}\""
            )

    for r in sorted(set(relasi)):
        baris.append(r)
    baris.append("")

    for model in models:
        baris.append(f"    {entitas(model)} {{")
        for field in model._meta.get_fields():
            if not getattr(field, "concrete", False):
                continue

            tipe = re.sub(r"\W", "", field.get_internal_type())
            nama = re.sub(r"\W", "_", field.name)
            if field.is_relation:
                nama = f"{nama}_id"

            kunci = ""
            if getattr(field, "primary_key", False):
                kunci = "PK"
            elif field.is_relation:
                kunci = "FK"
            elif getattr(field, "unique", False):
                kunci = "UK"

            catatan = []
            if getattr(field, "max_length", None):
                catatan.append(f"max {field.max_length}")
            if getattr(field, "choices", None):
                nilai = "|".join(str(c[0]) for c in field.choices)
                catatan.append(nilai[:44])
            if getattr(field, "null", False):
                catatan.append("null")
            if getattr(field, "blank", False):
                catatan.append("blank")
            if not getattr(field, "editable", True):
                catatan.append("editable=False")
            if field.has_default():
                d = field.get_default()
                catatan.append(f"default {getattr(d, '__name__', d)}")

            kolom = f"        {tipe} {nama}"
            if kunci:
                kolom += f" {kunci}"
            c = komentar(catatan)
            if c:
                kolom += f' "{c}"'
            baris.append(kolom)
        baris.append("    }")
        baris.append("")

    if not models:
        baris.append(f"    UNKNOWN_TIDAK_ADA_MODEL {{")
        baris.append(f"        string catatan \"app {nama_app} tidak punya model\"")
        baris.append("    }")

    return "\n".join(baris)


# --------------------------------------------------------------------------
# 2. stateDiagram — telusur AST
# --------------------------------------------------------------------------

def telusur_ast(dir_app):
    """Cari penulisan STATE_FIELD dan pemeriksaan RULE_FIELD di seluruh .py."""
    tulis_state = []
    baca_rule = []

    for akar, dirs, berkas in os.walk(dir_app):
        dirs[:] = [d for d in dirs if d not in {"migrations", "__pycache__", "tests"}]
        for nama in berkas:
            if not nama.endswith(".py"):
                continue
            path = os.path.join(akar, nama)
            rel = os.path.relpath(path, os.getcwd()).replace("\\", "/")
            try:
                with open(path, encoding="utf-8") as f:
                    pohon = ast.parse(f.read(), filename=path)
            except (SyntaxError, UnicodeDecodeError):
                continue

            for node in ast.walk(pohon):
                # penulisan: obj.selesai = X   /   Model(selesai=X)  /  update(selesai=X)
                if isinstance(node, ast.Assign):
                    for t in node.targets:
                        if isinstance(t, ast.Attribute) and t.attr == STATE_FIELD:
                            tulis_state.append((rel, node.lineno, "assign"))
                elif isinstance(node, ast.keyword) and node.arg == STATE_FIELD:
                    tulis_state.append((rel, node.lineno, "kwarg"))

                # pembacaan aturan
                if isinstance(node, ast.Attribute) and node.attr == RULE_FIELD:
                    baca_rule.append((rel, node.lineno))
                elif isinstance(node, ast.Constant) and node.value == RULE_FIELD:
                    baca_rule.append((rel, node.lineno))

    return sorted(set(tulis_state)), sorted(set(baca_rule))


def bangun_state(models, dir_app):
    tulis, rule = telusur_ast(dir_app)

    punya_state = [m for m in models if any(
        f.name == STATE_FIELD for f in m._meta.get_fields() if getattr(f, "concrete", False)
    )]
    pilihan_rule = []
    for m in models:
        for f in m._meta.get_fields():
            if getattr(f, "concrete", False) and f.name == RULE_FIELD and getattr(f, "choices", None):
                pilihan_rule = [str(c[0]) for c in f.choices]

    baris = ["stateDiagram-v2"]

    if not punya_state:
        baris.append(f"    [*] --> UNKNOWN : field '{STATE_FIELD}' tidak ditemukan")
        baris.append("    note right of UNKNOWN")
        baris.append(f"        Tidak ada model dengan field {STATE_FIELD}.")
        baris.append("        Siklus hidup belum bisa direkonstruksi.")
        baris.append("    end note")
        return "\n".join(baris)

    baris += [
        f"    [*] --> Terbuka : {STATE_FIELD} = False",
        f"    Terbuka --> Selesai : {STATE_FIELD} = True",
        "",
        "    note right of Terbuka",
        f"        Penulisan {STATE_FIELD} ditemukan di {len(tulis)} lokasi:",
    ]
    if tulis:
        for berkas, ln, jenis in tulis[:12]:
            baris.append(f"        {berkas}:{ln} ({jenis})")
        if len(tulis) > 12:
            baris.append(f"        ... dan {len(tulis) - 12} lainnya")
    else:
        baris.append("        TIDAK ADA. Field ini tidak pernah ditulis kode")
        baris.append("        mana pun - kemungkinan hanya diubah lewat admin")
        baris.append("        atau serializer generik. TEMUAN.")
    baris.append("    end note")
    baris.append("")

    baris.append("    note left of Selesai")
    if pilihan_rule:
        baris.append(f"        {RULE_FIELD}: {' | '.join(pilihan_rule)}")
    else:
        baris.append(f"        UNKNOWN: field {RULE_FIELD} tidak ditemukan")
    if rule:
        baris.append(f"        Dibaca di {len(rule)} lokasi:")
        for berkas, ln in rule[:10]:
            baris.append(f"        {berkas}:{ln}")
        if len(rule) > 10:
            baris.append(f"        ... dan {len(rule) - 10} lainnya")
    else:
        baris.append("        TIDAK PERNAH DIBACA kode mana pun.")
        baris.append("        Aturan penyelesaian tidak ditegakkan -")
        baris.append("        field ini dekoratif. TEMUAN.")
    baris.append("    end note")
    baris.append("")
    baris.append("    note right of Selesai")
    baris.append("        UNKNOWN: apakah ada transisi balik Selesai -> Terbuka.")
    baris.append("        Periksa manual apakah ada endpoint 'buka kembali'.")
    baris.append("    end note")

    return "\n".join(baris)


# --------------------------------------------------------------------------
# 3. flowchart — dari URL resolver
# --------------------------------------------------------------------------

def kumpulkan_rute(nama_app):
    """Telusuri URLconf, ambil rute yang callback-nya milik app ini."""
    from django.urls import get_resolver
    from django.urls.resolvers import URLPattern, URLResolver

    hasil = []

    def jalan(resolver, awalan=""):
        for p in resolver.url_patterns:
            pola = awalan + str(p.pattern)
            if isinstance(p, URLResolver):
                jalan(p, pola)
            elif isinstance(p, URLPattern):
                cb = p.callback
                modul = getattr(cb, "__module__", "") or ""
                cls = getattr(cb, "cls", None)
                if cls is not None:
                    modul = cls.__module__
                if modul.split(".")[0] != nama_app:
                    continue
                hasil.append((pola, cb, cls))

    try:
        jalan(get_resolver())
    except Exception as e:  # noqa: BLE001
        print(f"  ! gagal menelusuri URLconf: {e}", file=sys.stderr)
    return hasil


def punya_atomic(cls):
    """Cek apakah source kelas view menyebut transaction.atomic."""
    if cls is None:
        return None
    try:
        return "atomic" in inspect.getsource(cls)
    except (OSError, TypeError):
        return None


def bangun_flow(nama_app):
    rute = kumpulkan_rute(nama_app)
    baris = ["flowchart LR"]

    if not rute:
        baris.append("    UNKNOWN[\"Tidak ada rute milik app ini\"]")
        return "\n".join(baris)

    per_view = defaultdict(list)
    for pola, cb, cls in rute:
        kunci = cls.__name__ if cls is not None else getattr(cb, "__name__", "UNKNOWN")
        per_view[kunci].append((pola, cb, cls))

    tanpa_izin = []
    tanpa_atomic = []

    for nama_view, entri in sorted(per_view.items()):
        cls = entri[0][2]
        vid = id_aman(f"v_{nama_view}")

        baris.append(f"    subgraph sg_{vid}[\"{label_aman(nama_view)}\"]")
        baris.append("        direction LR")

        # URL
        for i, (pola, cb, _c) in enumerate(entri):
            uid = id_aman(f"u_{nama_view}_{i}")
            baris.append(f"        {uid}[/\"/{label_aman(pola)}\"/]")
            baris.append(f"        {uid} --> {vid}")

        izin = getattr(cls, "permission_classes", None) if cls else None
        teks_izin = ", ".join(p.__name__ for p in izin) if izin else "TANPA PERMISSION"
        if not izin:
            tanpa_izin.append(nama_view)

        atomic = punya_atomic(cls)
        teks_atomic = {True: "atomic", False: "TANPA atomic", None: "UNKNOWN atomic"}[atomic]
        if atomic is False:
            tanpa_atomic.append(nama_view)

        baris.append(f"        {vid}[\"{label_aman(nama_view)}<br/>{teks_izin}<br/>{teks_atomic}\"]")

        ser = getattr(cls, "serializer_class", None) if cls else None
        if ser is not None:
            sid = id_aman(f"s_{ser.__name__}")
            baris.append(f"        {sid}[\"{label_aman(ser.__name__)}\"]")
            baris.append(f"        {vid} --> {sid}")
            berikut = sid
        else:
            sid = id_aman(f"s_{nama_view}_unknown")
            baris.append(f"        {sid}[\"UNKNOWN serializer\"]")
            baris.append(f"        {vid} --> {sid}")
            berikut = sid

        model = None
        qs = getattr(cls, "queryset", None) if cls else None
        if qs is not None:
            model = qs.model
        elif ser is not None:
            model = getattr(getattr(ser, "Meta", None), "model", None)

        if model is not None:
            mid = id_aman(f"m_{model.__name__}")
            baris.append(f"        {mid}[(\"{label_aman(model.__name__)}\")]")
            baris.append(f"        {berikut} --> {mid}")
        else:
            mid = id_aman(f"m_{nama_view}_unknown")
            baris.append(f"        {mid}[(\"UNKNOWN model\")]")
            baris.append(f"        {berikut} --> {mid}")

        baris.append("    end")
        baris.append("")

    baris.append("    classDef bahaya fill:#FCEBEB,stroke:#A32D2D,color:#501313")
    baris.append("    classDef awas fill:#FAEEDA,stroke:#854F0B,color:#412402")
    if tanpa_izin:
        baris.append("    class " + ",".join(id_aman(f"v_{v}") for v in tanpa_izin) + " bahaya")
    if tanpa_atomic:
        baris.append("    class " + ",".join(id_aman(f"v_{v}") for v in tanpa_atomic) + " awas")

    return "\n".join(baris)


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Generator Mermaid AS-IS dari kode Django.")
    ap.add_argument("--app", default=DEFAULT_APP, help=f"label app (default: {DEFAULT_APP})")
    ap.add_argument("--settings", default=None, help="DJANGO_SETTINGS_MODULE")
    ap.add_argument("--out", default=None, help="direktori keluaran (default: folder skrip ini)")
    arg = ap.parse_args()

    settings_module = arg.settings or deteksi_settings()
    if not settings_module:
        sys.exit("Tidak menemukan DJANGO_SETTINGS_MODULE. Pakai --settings.")

    print(f"settings : {settings_module}")
    setup_django(settings_module)

    from django.apps import apps

    try:
        cfg = apps.get_app_config(arg.app)
    except LookupError:
        terdaftar = ", ".join(sorted(a.label for a in apps.get_app_configs()))
        sys.exit(f"App '{arg.app}' tidak ada di INSTALLED_APPS.\nTerdaftar: {terdaftar}")

    models = list(cfg.get_models())
    dir_app = cfg.path
    out = arg.out or os.path.dirname(os.path.abspath(__file__))
    os.makedirs(out, exist_ok=True)

    print(f"app      : {cfg.label}  ({len(models)} model)")
    print(f"path     : {dir_app}")
    print(f"keluaran : {out}\n")

    berkas = {
        "01-asis-er.mmd": bangun_er(models, arg.app),
        "01-asis-state.mmd": bangun_state(models, dir_app),
        "01-asis-flow.mmd": bangun_flow(arg.app),
    }

    for nama, isi in berkas.items():
        path = os.path.join(out, nama)
        with open(path, "w", encoding="utf-8") as f:
            f.write(isi + "\n")
        print(f"  tulis {nama}  ({len(isi.splitlines())} baris)")

    print("\n" + "=" * 70)
    for nama, isi in berkas.items():
        print(f"\n----- {nama} " + "-" * (60 - len(nama)))
        print(isi)


if __name__ == "__main__":
    main()
