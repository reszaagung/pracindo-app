"""
Membangun daftar endpoint kanonik yang diperkaya: graph/endpoints.json

Basis = hasil telusur resolver di graph/_reconcile.json (sumber kebenaran = kode).
Atribut permission/status/atomic diambil dari analisis FASE 1 scan sebelumnya,
setiap nilai punya rujukan file:baris di 01-api-map.md.

Jalankan:  python docs/_scan/graph/_endpoints.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SCAN = os.path.dirname(HERE)

# ---------------------------------------------------------------------------
# 16 operasi tulis yang SELALU membalas 405 (ghost)
GHOST = {
    ("PUT", "/api/v1/akunting/purchase-order/{id}/"),
    ("PATCH", "/api/v1/akunting/purchase-order/{id}/"),
    ("DELETE", "/api/v1/akunting/purchase-order/{id}/"),
    ("POST", "/api/v1/akunting/faktur/"),
    ("PUT", "/api/v1/akunting/faktur/{id}/"),
    ("PATCH", "/api/v1/akunting/faktur/{id}/"),
    ("DELETE", "/api/v1/akunting/faktur/{id}/"),
    ("PUT", "/api/v1/warehouse/penerimaan/{id}/"),
    ("PATCH", "/api/v1/warehouse/penerimaan/{id}/"),
    ("DELETE", "/api/v1/warehouse/penerimaan/{id}/"),
    ("PUT", "/api/v1/warehouse/laporan-selisih/{id}/"),
    ("PATCH", "/api/v1/warehouse/laporan-selisih/{id}/"),
    ("DELETE", "/api/v1/warehouse/laporan-selisih/{id}/"),
    ("PUT", "/api/v1/produksi/sesi/{id}/"),
    ("PATCH", "/api/v1/produksi/sesi/{id}/"),
    ("DELETE", "/api/v1/produksi/sesi/{id}/"),
}

# 3 DELETE yang membalas 400 (perform_destroy raise), bukan 405
ALWAYS_400 = {
    ("DELETE", "/api/v1/auth/profil/{id}/"),
    ("DELETE", "/api/v1/master/produk/{id}/"),
    ("DELETE", "/api/v1/master/suplier/{id}/"),
}

# permission per view; nilai khusus per action menimpa default
PERM = {
    "staff_user.views.DaftarView": ("AllowAny", {}),
    "staff_user.views.LoginView": ("AllowAny", {}),
    "staff_user.views.LogoutView": ("SudahLogin", {}),
    "staff_user.views.PortalView": ("SudahLogin", {}),
    "staff_user.views.GantiPasswordView": ("SudahLogin", {}),
    "staff_user.views.ProfilViewSet": ("AksesModul:staff_user", {
        "create": "HanyaAdmin", "destroy": "HanyaAdmin",
        "saya": "SudahLogin", "menunggu": "HanyaSupervisor",
        "aktifkan": "HanyaSupervisor", "tolak": "HanyaSupervisor",
        "ubah_role": "HanyaSupervisor", "nonaktifkan": "HanyaSupervisor",
        "aktifkan_kembali": "HanyaSupervisor", "reset_password": "HanyaSupervisor",
    }),
    "staff_user.views.JabatanViewSet": ("AksesModul:staff_user", {}),
    "staff_user.views.DataKepegawaianViewSet": ("SudahLogin+DiriSendiriAtauSupervisor", {}),
    "staff_user.views.RiwayatAksesViewSet": ("HanyaSupervisor", {}),
    "master.views.ProdukViewSet": ("AdminAtauAkunting", {
        "list": "SudahLogin", "retrieve": "SudahLogin"}),
    "master.views.SuplierViewSet": ("AdminAtauAkunting", {
        "list": "SudahLogin", "retrieve": "SudahLogin"}),
    "core.views.EntitasViewSet": ("HanyaSupervisor", {}),
    "core.views.GrupBahanViewSet": ("HanyaSupervisor", {}),
    "core.views.PeriodeAkuntansiViewSet": ("SudahLogin", {
        "tutup": "HanyaSupervisor", "buka": "HanyaSupervisor"}),
    "inventory.views.StokViewSet": ("AksesModul:inventory", {}),
    "inventory.views.TangkiViewSet": ("AksesModul:inventory", {}),
    "inventory.views.MutasiStokViewSet": ("AksesModul:inventory", {}),
    "inventory.views.PosisiKlaimViewSet": ("AksesModul:inventory", {}),
    "inventory.views.NilaiEkuivalenViewSet": ("AksesModul:inventory", {}),
    "inventory.views.IsiPoolView": ("AksesModul:inventory", {}),
    "inventory.views.SetorKePoolView": ("PunyaRole:GUDANG,PRODUKSI", {}),
    "inventory.views.KlaimHasilView": ("PunyaRole:GUDANG,PRODUKSI", {}),
    "inventory.views.OpnameView": ("HanyaSupervisor", {}),
    "inventory.views.VerifikasiView": ("HanyaSupervisor", {}),
    "akunting.views.AkunViewSet": ("AksesModul:akunting", {}),
    "akunting.views.JurnalUmumViewSet": ("AksesModul:akunting", {"balik": "PunyaRole:SUPERVISOR"}),
    "akunting.views.PurchaseOrderViewSet": ("AksesModul:akunting", {}),
    "akunting.views.FakturPembelianViewSet": ("AksesModul:akunting", {}),
    "akunting.views.PembayaranView": ("AksesModul:keuangan", {}),
    "akunting.views.UangMukaViewSet": ("AksesModul:keuangan", {}),
    "keuangan.views.PengeluaranViewSet": ("NONE->IsAuthenticated", {}),
    "warehouse.views.POSiapTerimaViewSet": ("AksesModul:warehouse", {}),
    "warehouse.views.PenerimaanViewSet": ("AksesModul:warehouse", {}),
    "warehouse.views.LaporanSelisihViewSet": ("AksesModul:warehouse", {
        "selesaikan": "AksesModul:warehouse+cek akunting",
        "tutup": "AksesModul:warehouse+cek akunting"}),
    "warehouse.views.PackagingViewSet": ("AksesModul:warehouse", {}),
    "produksi.views.SesiViewSet": ("AksesModul:produksi", {}),
    "work_order.views.WorkOrderViewSet": ("IsAuthenticated", {}),
    "drf_spectacular.views.SpectacularAPIView": ("IsAuthenticated(default)", {}),
    "drf_spectacular.views.SpectacularSwaggerView": ("IsAuthenticated(default)", {}),
}

# endpoint tulis yang seluruh efek sampingnya dibungkus transaction.atomic
ATOMIC_OK = {
    "/api/v1/auth/daftar/", "/api/v1/auth/register/", "/api/v1/auth/ganti-password/",
    "/api/v1/core/periode/tutup/", "/api/v1/core/periode/buka/",
    "/api/v1/inventory/setor-ke-pool/", "/api/v1/inventory/klaim-hasil/",
    "/api/v1/inventory/opname/",
    "/api/v1/akunting/purchase-order/", "/api/v1/akunting/pembayaran/",
    "/api/v1/warehouse/penerimaan/", "/api/v1/warehouse/laporan-selisih/",
    "/api/v1/produksi/sesi/", "/api/v1/keuangan/pengeluaran/",
}
ATOMIC_ACTIONS = {
    "balik", "ubah_item", "kirim", "batalkan", "dari_penerimaan",
    "aktifkan", "tolak", "ubah_role", "nonaktifkan", "aktifkan_kembali",
    "reset_password", "ajukan", "selesaikan", "tutup", "mulai",
}
# endpoint tulis yang TIDAK dibungkus atomic penuh (temuan FASE 1 §C)
ATOMIC_BROKEN = {
    ("POST", "/api/v1/work-order/"),
    ("POST", "/api/v1/produksi/sesi/{id}/mulai/"),
    ("POST", "/api/v1/auth/login/"),
}

APP_OF_PREFIX = [
    ("/api/v1/auth/", "staff_user"), ("/api/v1/master/", "master"),
    ("/api/v1/inventory/", "inventory"), ("/api/v1/akunting/", "akunting"),
    ("/api/v1/keuangan/", "keuangan"), ("/api/v1/warehouse/", "warehouse"),
    ("/api/v1/produksi/", "produksi"), ("/api/v1/work-order/", "work_order"),
    ("/api/v1/core/", "core"), ("/api/", "pracindo_erp"),
]
WRITE = {"POST", "PUT", "PATCH", "DELETE"}


def app_of(path):
    for pre, app in APP_OF_PREFIX:
        if path.startswith(pre):
            return app
    return "UNKNOWN"


def main():
    rec = json.load(open(os.path.join(HERE, "_reconcile.json"), encoding="utf-8"))
    out = []
    for r in rec["resolver"]:
        m, p, view, action = r["method"], r["path"], r["view"], r["action"]
        default, per_action = PERM.get(view, ("UNKNOWN", {}))
        perm = per_action.get(action, default)
        if (m, p) in GHOST:
            status = "ghost"
        elif view.startswith("work_order."):
            status = "dead"          # modul tidak berfungsi (H2: profil_staff_id)
        else:
            status = "live"
        if m in WRITE and status == "live":
            if (m, p) in ATOMIC_BROKEN:
                atomic = False
            elif p in ATOMIC_OK or action in ATOMIC_ACTIONS:
                atomic = True
            else:
                atomic = False
        else:
            atomic = None
        out.append({
            "method": m, "path": p, "view": view, "action": action,
            "url_name": r["url_name"], "app": app_of(p),
            "permission": perm, "status": status,
            "write": m in WRITE, "atomic": atomic,
            # menulis >1 tabel TANPA transaction.atomic (FASE 1 §C) - ini yang berbahaya,
            # berbeda dari CRUD 1 tabel yang memang tidak butuh atomic
            "multi_table_no_atomic": (m, p) in ATOMIC_BROKEN,
            "always_400": (m, p) in ALWAYS_400,
        })
    out.sort(key=lambda d: (d["path"], d["method"]))
    json.dump(out, open(os.path.join(HERE, "endpoints.json"), "w", encoding="utf-8"),
              indent=1, ensure_ascii=False)

    from collections import Counter
    print("total endpoint kanonik :", len(out))
    print("per status             :", dict(Counter(d["status"] for d in out)))
    print("per app                :", dict(Counter(d["app"] for d in out)))
    print("permission NONE/AllowAny:",
          sum(1 for d in out if d["permission"] in ("NONE->IsAuthenticated", "AllowAny")))
    print("write tanpa atomic     :",
          [(d["method"], d["path"]) for d in out if d["write"] and d["atomic"] is False])
    print("permission UNKNOWN     :",
          [(d["method"], d["path"], d["view"]) for d in out if d["permission"] == "UNKNOWN"])


if __name__ == "__main__":
    main()
