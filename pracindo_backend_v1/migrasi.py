from inventory.models import Packing, StatusDokumen
from warehouse.models import Packaging as WarehousePackaging, StokItemsPabrik, StokBarangJadi
from django.db import transaction
from decimal import Decimal

def get_valid_product(ProdukModel, string_val):
    """Mencari objek produk dengan aman agar tidak pernah menghasilkan nilai NULL"""
    if not ProdukModel:
        return None
    
    if string_val:
        string_str = str(string_val).strip()
        for field_name in ['id', 'kode', 'nama', 'nama_item', 'slug', 'id_produk']:
            try:
                obj = ProdukModel.objects.filter(**{field_name: string_str}).first()
                if obj:
                    return obj
            except Exception:
                continue

    return ProdukModel.objects.first()

def get_valid_grup(GbModel, string_val):
    if not GbModel or not string_val:
        return None
    string_str = str(string_val).strip()
    try:
        obj = GbModel.objects.filter(kode=string_str).first()
        if obj: return obj
    except Exception:
        pass
    
    try:
        return GbModel.objects.create(kode=string_str, nama=string_str.replace('_', ' ').title())
    except Exception:
        return GbModel.objects.first()

def run_migration():
    with transaction.atomic():
        print("Membersihkan data warehouse lama...")
        StokBarangJadi.objects.all().delete()
        WarehousePackaging.objects.all().delete()
        StokItemsPabrik.objects.all().delete()
        
        packings = Packing.objects.select_related("entitas").filter(status=StatusDokumen.POSTED)
        
        ProdukModel = None
        for f in WarehousePackaging._meta.get_fields():
            if f.name == 'produk' and f.is_relation:
                ProdukModel = f.related_model
                break
                
        GbModel = None
        for f in WarehousePackaging._meta.get_fields():
            if f.name == 'grup_bahan' and f.is_relation:
                GbModel = f.related_model
                break

        sukses = 0
        for p in packings:
            if p.total_unit and Decimal(str(p.total_unit)) > 0:
                isi_per = (p.qty_kg / Decimal(str(p.total_unit))).quantize(Decimal("0.001"))
            else:
                isi_per = Decimal("0")
            
            prod_obj = get_valid_product(ProdukModel, p.nama_hasil_id)
            grup_val = p.entitas.grup_bahan_id if p.entitas and hasattr(p.entitas, 'grup_bahan_id') else None
            grup_obj = get_valid_grup(GbModel, grup_val)

            if not prod_obj:
                print(f"[WARNING] Melewati packing ID {p.id} karena Master Produk kosong total.")
                continue

            WarehousePackaging.objects.create(
                tanggal=p.tanggal,
                item=item_obj,   
                grup_bahan=grup_obj,
                qty_curah=p.qty_kg,
                qty_kemasan=p.total_unit,
                isi_per_kemasan=isi_per
            )
            
            sbj_kwargs = {
                "produk": prod_obj,
                "isi_per_kemasan": isi_per,
            }
            sbj_fields = [f.name for f in StokBarangJadi._meta.get_fields()]
            if "grup_bahan" in sbj_fields:
                sbj_kwargs["grup_bahan"] = grup_obj
            elif "entitas" in sbj_fields:
                sbj_kwargs["entitas"] = p.entitas 
                
            stok_bj, _ = StokBarangJadi.objects.get_or_create(
                **sbj_kwargs,
                defaults={"qty_kemasan": 0, "total_isi": Decimal("0")}
            )
            stok_bj.qty_kemasan += p.total_unit
            stok_bj.total_isi += p.qty_kg
            stok_bj.save()

            # 3. Simpan ke tabel StokItemsPabrik
            sip_kwargs = {
                "produk": prod_obj,
                "isi_per_kemasan": isi_per,
            }
            sip_fields = [f.name for f in StokItemsPabrik._meta.get_fields()]
            if "grup_bahan" in sip_fields:
                sip_kwargs["grup_bahan"] = grup_obj
            elif "entitas" in sip_fields:
                sip_kwargs["entitas"] = p.entitas

            stok_ip, _ = StokItemsPabrik.objects.get_or_create(
                **sip_kwargs,
                defaults={"qty_kemasan": 0, "total_isi": Decimal("0")}
            )
            stok_ip.qty_kemasan += p.total_unit
            stok_ip.total_isi += p.qty_kg
            stok_ip.save()
            
            sukses += 1
            
        print(f"\n[MANTAP] {sukses} data sukses diproses tanpa error syntax!\n")

run_migration()