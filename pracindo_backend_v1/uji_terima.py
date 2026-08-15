import datetime, traceback
from django.contrib.auth import get_user_model
from akunting.models import PurchaseOrder
from warehouse.services import terima_barang
from inventory.models import SaldoPool, MutasiKlaim, Pembelian
from inventory.services import jalankan_pemeriksaan_invarian

po = PurchaseOrder.objects.first()
if po is None:
    print("TIDAK ADA PO. Buat dulu lewat admin.")
    raise SystemExit
it = po.item.first()

print("=" * 62)
print("PO     :", po)
print("entitas:", getattr(po, "entitas", None))
print("item   :", it.nama_item)
print("produk :", getattr(it, "produk", "FIELD TIDAK ADA"))
print("harga  :", getattr(it, "harga_per_kg", "FIELD TIDAK ADA"))
print("sisa   :", it.sisa_qty)
print("-" * 62)

try:
    p, l, s = terima_barang(
        po_id=po.id, no_surat_jalan="SJ-UJI-" + datetime.datetime.now().strftime("%H%M%S"),
        tanggal=datetime.date.today(), user=get_user_model().objects.first(),
        baris=[{"po_item_id": it.id, "jenis_kemasan": "KARUNG",
                "jumlah_koli": 2, "isi_per_koli": "50.000",
                "qty_diterima": "98.000", "qty_ditolak": "0"}])
    print("penerimaan:", p.nomor)
    print("selisih   :", [(x.nomor, x.jenis, str(x.qty_selisih)) for x in l])
    print("setoran   :", [(x.nomor, str(x.qty_kg), str(x.nilai)) for x in s])
except Exception:
    traceback.print_exc()

print("-" * 62)
print("pembelian :", Pembelian.objects.count())
for x in SaldoPool.objects.select_related("grup_bahan", "produk"):
    print("POOL      :", x.grup_bahan.kode, x.produk, x.qty_kg, x.nilai)
for m in MutasiKlaim.objects.select_related("entitas"):
    print("KLAIM     :", m.entitas.kode, m.tipe, m.arah, m.qty_kg, m.nilai)
print("-" * 62)
print(jalankan_pemeriksaan_invarian())
print("=" * 62)
