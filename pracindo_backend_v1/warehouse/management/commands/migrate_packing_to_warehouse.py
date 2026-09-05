from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction

# Sesuaikan import dengan struktur project yang sebenarnya
from inventory.models import Packing, Kemasan, StatusDokumen
from warehouse.models import Packaging, StokItemsPabrik
# Asumsi model StokBarangJadi ada di warehouse.models
from warehouse.models import StokBarangJadi 

class Command(BaseCommand):
    help = 'Migrasi data Packing dari modul Inventory ke modul Warehouse'

    def handle(self, *args, **options):
        self.stdout.write("Memulai proses migrasi Packing ke Warehouse...")

        # 1. Ambil master kemasan aktif ke memory (untuk meminimalisir query dalam loop)
        master_kemasan_aktif = list(Kemasan.objects.filter(aktif=True))
        
        # Dictionary untuk agregasi stok (Rule 4 & 10)
        agregasi_stok_bj = {}     # Key: (entitas_id, grup_bahan_id, item_id, kemasan_id)
        agregasi_stok_items = {}  # Key: (produk_id, isi_per_kemasan)
        
        packaging_to_create = []
        error_logs = []
        skipped_count = 0

        # Ambil data packing berstatus POSTED sesuai PRD[cite: 1]
        packings = Packing.objects.filter(
            status=StatusDokumen.POSTED
        ).select_related(
            'entitas', 'entitas__grup_bahan', 'nama_hasil', 'kemasan', 'kemasan__produk'
        )

        with transaction.atomic():
            self.stdout.write("Menghapus data target lama (Idempotensi)...")
            Packaging.objects.all().delete()
            StokBarangJadi.objects.all().delete()
            StokItemsPabrik.objects.all().delete()

            for packing in packings:
                # Rule 16: Validasi Sebelum Migrasi
                if packing.total_unit <= 0 or packing.qty_kg < 0:
                    skipped_count += 1
                    error_logs.append(f"SKIP {packing.nomor}: total_unit atau qty_kg tidak valid.")
                    continue
                
                if not getattr(packing, 'entitas', None) or not getattr(packing, 'nama_hasil', None) or not getattr(packing, 'kemasan', None) or not getattr(packing.kemasan, 'produk', None):
                    skipped_count += 1
                    error_logs.append(f"SKIP {packing.nomor}: Relasi FK ada yang kosong (entitas/nama_hasil/kemasan/produk).")
                    continue

                # 1. Hitung isi per kemasan
                isi_per_kemasan = packing.qty_kg / Decimal(packing.total_unit)

                # 2. Cari klasifikasi Kemasan (Rule 2 & 5 & 6)
                kemasan_cocok_id = None
                for mk in master_kemasan_aktif:
                    if abs(mk.bobot_kg - isi_per_kemasan) <= Decimal("0.001"):
                        kemasan_cocok_id = mk.id
                        break
                
                if kemasan_cocok_id is None:
                    error_logs.append(f"WARNING {packing.nomor}: Tidak ada master Kemasan cocok untuk bobot {isi_per_kemasan:.3f} kg. Record StokBarangJadi dilewati.")
                    # PRD Rule 6: record target yang butuh kemasan dilewati/null.

                # 3. Build object WarehousePackaging
                grup_bahan_id = packing.entitas.grup_bahan_id
                
                packaging_to_create.append(
                    Packaging(
                        tanggal=packing.tanggal,
                        item_id=packing.nama_hasil_id,
                        grup_bahan_id=grup_bahan_id,
                        qty_curah=packing.qty_kg,
                        qty_kemasan=packing.total_unit,
                        isi_per_kemasan=isi_per_kemasan,
                    )
                )

                # 4. Agregasi StokBarangJadi (Rule 8, 9, 10)
                if kemasan_cocok_id is not None:
                    key_bj = (
                        packing.entitas_id,
                        grup_bahan_id,
                        packing.nama_hasil_id,
                        kemasan_cocok_id
                    )
                    if key_bj not in agregasi_stok_bj:
                        agregasi_stok_bj[key_bj] = {
                            'qty_unit': 0,
                            'qty_kg': Decimal("0.000")
                        }
                    agregasi_stok_bj[key_bj]['qty_unit'] += packing.total_unit
                    agregasi_stok_bj[key_bj]['qty_kg'] += packing.qty_kg

                # 5. Agregasi StokItemsPabrik (Rule 11 & 12)
                # Note: target produk berasal dari PoolKemasan.produk
                key_items = (
                    packing.kemasan.produk_id,
                    isi_per_kemasan
                )
                if key_items not in agregasi_stok_items:
                    agregasi_stok_items[key_items] = {
                        'qty_kemasan': 0,
                        'total_isi': Decimal("0.000")
                    }
                agregasi_stok_items[key_items]['qty_kemasan'] += packing.total_unit
                agregasi_stok_items[key_items]['total_isi'] += packing.qty_kg

            # --- INSERT HASIL KE DATABASE ---
            self.stdout.write(f"Menyimpan {len(packaging_to_create)} record WarehousePackaging...")
            Packaging.objects.bulk_create(packaging_to_create, batch_size=1000)

            self.stdout.write(f"Menyimpan {len(agregasi_stok_bj)} record StokBarangJadi...")
            stok_bj_to_create = [
                StokBarangJadi(
                    entitas_id=k[0],
                    grup_bahan_id=k[1],
                    item_id=k[2],
                    kemasan=k[3], # Menyimpan integer ID Kemasan
                    qty_unit=v['qty_unit'],
                    qty_kg=v['qty_kg']
                ) for k, v in agregasi_stok_bj.items()
            ]
            StokBarangJadi.objects.bulk_create(stok_bj_to_create, batch_size=1000)

            self.stdout.write(f"Menyimpan {len(agregasi_stok_items)} record StokItemsPabrik...")
            stok_items_to_create = [
                StokItemsPabrik(
                    produk_id=k[0],
                    isi_per_kemasan=k[1],
                    qty_kemasan=v['qty_kemasan'],
                    total_isi=v['total_isi']
                ) for k, v in agregasi_stok_items.items()
            ]
            StokItemsPabrik.objects.bulk_create(stok_items_to_create, batch_size=1000)

        # --- SUMMARY LOGS ---
        self.stdout.write(self.style.SUCCESS("Migrasi Selesai!"))
        self.stdout.write(f"Total Packaging diproses  : {len(packaging_to_create)}")
        self.stdout.write(f"Total StokBarangJadi      : {len(stok_bj_to_create)}")
        self.stdout.write(f"Total StokItemsPabrik     : {len(stok_items_to_create)}")
        self.stdout.write(f"Total dilewati (Invalid)  : {skipped_count}")
        
        if error_logs:
            self.stdout.write(self.style.WARNING(f"\nTerdapat {len(error_logs)} catatan/peringatan:"))
            for log in error_logs[:20]: # Tampilkan max 20 log
                self.stdout.write(self.style.WARNING(f" - {log}"))
            if len(error_logs) > 20:
                self.stdout.write(self.style.WARNING(" - ... (sisa log disembunyikan)"))