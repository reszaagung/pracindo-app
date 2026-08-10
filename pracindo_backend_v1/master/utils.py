# master/utils.py

def generate_kode_urut(model_class, prefix, field_name='kode', padding=4):
    """
    Fungsi reusable untuk generate kode berurutan.
    Contoh output jika prefix="BP", padding=4: BP-0001, BP-0002
    """
    # Cari data terakhir yang kodenya diawali prefix
    last_obj = model_class.objects.filter(
        **{f"{field_name}__startswith": f"{prefix}-"}
    ).order_by(field_name).last()

    if last_obj:
        last_kode = getattr(last_obj, field_name)
        try:
            # Pecah "BP-0011" menjadi ["BP", "0011"], lalu ambil angka terakhir
            last_number = int(last_kode.split('-')[1])
            new_number = last_number + 1
        except (IndexError, ValueError):
            new_number = 1
    else:
        new_number = 1

    # Format angka dengan padding nol (contoh: 0012)
    return f"{prefix}-{new_number:0{padding}d}"