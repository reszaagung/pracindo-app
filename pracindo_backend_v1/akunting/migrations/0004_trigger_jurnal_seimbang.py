"""
Trigger keseimbangan jurnal.

Invariant SUM(debit) = SUM(kredit) per jurnal tidak bisa ditegakkan lewat
CheckConstraint -- itu aturan lintas-baris, sementara CheckConstraint hanya
melihat satu baris.

Validasi di clean() juga tidak cukup: posting() memakai bulk_create yang
melewati clean() sepenuhnya, dan shell, migrasi, serta query manual bisa
menembusnya juga. Satu-satunya penjaga yang tidak bisa dilewati adalah
trigger di database.

DEFERRABLE INITIALLY DEFERRED adalah kuncinya. Tanpa itu trigger berjalan
per baris, dan baris debit pertama akan SELALU gagal karena baris kreditnya
belum ada. Dengan DEFERRED, pemeriksaan ditunda sampai COMMIT -- yang wajib
seimbang hanya kondisi akhir transaksi.

Simpan sebagai:
    akunting/migrations/0004_trigger_jurnal_seimbang.py
"""
from django.db import migrations

BUAT = r"""
CREATE OR REPLACE FUNCTION cek_jurnal_seimbang() RETURNS TRIGGER AS $$
DECLARE
    jid     BIGINT;
    selisih NUMERIC;
BEGIN
    jid := COALESCE(NEW.jurnal_id, OLD.jurnal_id);

    SELECT COALESCE(SUM(debit) - SUM(kredit), 0)
      INTO selisih
      FROM akunting_jurnal_detail
     WHERE jurnal_id = jid;

    IF selisih <> 0 THEN
        RAISE EXCEPTION
            'Jurnal % tidak seimbang. Selisih debit-kredit = %', jid, selisih
            USING ERRCODE = 'check_violation';
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE CONSTRAINT TRIGGER trg_jurnal_seimbang
    AFTER INSERT OR UPDATE OR DELETE ON akunting_jurnal_detail
    DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW EXECUTE FUNCTION cek_jurnal_seimbang();
"""

HAPUS = r"""
DROP TRIGGER IF EXISTS trg_jurnal_seimbang ON akunting_jurnal_detail;
DROP FUNCTION IF EXISTS cek_jurnal_seimbang();
"""


class Migration(migrations.Migration):

    dependencies = [
        ('akunting', '0003_initial'),
    ]

    operations = [
        migrations.RunSQL(sql=BUAT, reverse_sql=HAPUS),
    ]
