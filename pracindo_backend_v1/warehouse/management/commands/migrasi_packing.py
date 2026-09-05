from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from inventory.models import Packing, StatusDokumen
from warehouse.models import (
    Packaging as WarehousePackaging,
    StokItemsPabrik,
    StokBarangJadi,
)


class Command(BaseCommand):
    help = "Migrasi data Packing ke Warehouse dan update Stok"

    def handle(self, *args, **options):
        with transaction.atomic():
            self.stdout.write("Membersihkan data warehouse lama...")

            StokBarangJadi.objects.all().delete()
            WarehousePackaging.objects.all().delete()
            StokItemsPabrik.objects.all().delete()

            packings = (
                Packing.objects
                .select_related(
                    "entitas",
                    "kemasan",
                    "nama_hasil",
                )
                .filter(status=StatusDokumen.POSTED)
                .order_by("id")
            )

            sukses = 0
            dilewati = 0

            for p in packings:

                # ======================================================
                # VALIDASI
                # ======================================================

                if not p.total_unit or p.total_unit <= 0:
                    dilewati += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"Packing {p.pk} dilewati: total_unit tidak valid"
                        )
                    )
                    continue

                if not p.entitas_id:
                    dilewati += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"Packing {p.pk} dilewati: entitas kosong"
                        )
                    )
                    continue

                if not p.nama_hasil_id:
                    dilewati += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"Packing {p.pk} dilewati: nama_hasil kosong"
                        )
                    )
                    continue

                if not p.kemasan_id:
                    dilewati += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"Packing {p.pk} dilewati: kemasan kosong"
                        )
                    )
                    continue

                # ======================================================
                # HITUNG ISI PER KEMASAN
                # ======================================================

                isi_per = (
                    p.qty_kg / Decimal(str(p.total_unit))
                ).quantize(Decimal("0.001"))

                # MasterProduk -> dipakai WarehousePackaging.item
                master_produk_id = str(p.nama_hasil_id)

                # ======================================================
                # GRUP BAHAN
                # ======================================================

                grup_bahan_id = p.entitas.grup_bahan_id

                grup_obj = None

                if grup_bahan_id:
                    grup_obj = p.entitas.grup_bahan

                # ======================================================
                # 1. WAREHOUSE PACKAGING
                # ======================================================

                WarehousePackaging.objects.create(
                    tanggal=p.tanggal,
                    item_id=master_produk_id,
                    grup_bahan=grup_obj,
                    qty_curah=p.qty_kg,
                    qty_kemasan=p.total_unit,
                    isi_per_kemasan=isi_per,
                )

                # ======================================================
                # 2. STOK BARANG JADI
                #
                # entitas    = Entitas
                # grup_bahan = GrupBahan
                # item       = MasterProduk
                # kemasan    = IntegerField berisi PoolKemasan.id
                # ======================================================

                stok_bj, created = StokBarangJadi.objects.get_or_create(
                    entitas_id=p.entitas_id,
                    grup_bahan=grup_obj,
                    item_id=master_produk_id,
                    kemasan=p.kemasan_id,
                    defaults={
                        "qty_unit": 0,
                        "qty_kg": Decimal("0"),
                    },
                )

                stok_bj.qty_unit += p.total_unit
                stok_bj.qty_kg += p.qty_kg

                stok_bj.save(
                    update_fields=[
                        "qty_unit",
                        "qty_kg",
                    ]
                )

                # ======================================================
                # 3. STOK ITEMS PABRIK
                #
                # produk          = Produk (PK integer)
                # isi_per_kemasan = berat per kemasan
                # ======================================================

                if not p.kemasan.produk_id:
                    dilewati += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"Packing {p.pk} dilewati: "
                            f"PoolKemasan tidak memiliki produk"
                        )
                    )
                    continue

                stok_ip, created = StokItemsPabrik.objects.get_or_create(
                    produk_id=p.kemasan.produk_id,
                    isi_per_kemasan=isi_per,
                    defaults={
                        "qty_kemasan": 0,
                        "total_isi": Decimal("0"),
                    },
                )

                stok_ip.qty_kemasan += p.total_unit
                stok_ip.total_isi += p.qty_kg

                stok_ip.save(
                    update_fields=[
                        "qty_kemasan",
                        "total_isi",
                    ]
                )

                sukses += 1

            self.stdout.write("")

            self.stdout.write(
                self.style.SUCCESS(
                    f"[MANTAP] {sukses} data berhasil dimigrasikan."
                )
            )

            if dilewati:
                self.stdout.write(
                    self.style.WARNING(
                        f"[WARNING] {dilewati} data dilewati."
                    )
                )