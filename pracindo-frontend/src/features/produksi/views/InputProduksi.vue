<template>
  <div class="input-produksi">
    <header class="ip-header">
      <h1>Modul Produksi (Mixing &amp; Blending)</h1>
      <p v-if="mode === 'form'" class="ip-subtitle">
        {{ editingBatchId ? 'Ubah Draft Batch' : 'Buat Batch Baru' }} —
        {{ jenisProduksi === JENIS.MIXING ? 'Mixing' : 'Blending' }}
      </p>
    </header>

    <p v-if="errorMsg" class="ip-alert ip-alert--error">{{ errorMsg }}</p>

    <!-- ================= MODE: LIST ================= -->
    <section v-if="mode === 'list'" class="ip-list">
      <div class="ip-toolbar">
        <div class="ip-filter">
          <select v-model="filter.jenis" @change="muatDaftarBatch">
            <option value="">Semua Jenis</option>
            <option value="MIXING">Mixing</option>
            <option value="BLENDING">Blending</option>
          </select>
          <select v-model="filter.status" @change="muatDaftarBatch">
            <option value="">Semua Status</option>
            <option value="DRAFT">Draft</option>
            <option value="POSTED">Posted</option>
            <option value="VOID">Void</option>
          </select>
          <input
            v-model="filter.search"
            type="text"
            placeholder="Cari batch / nama hasil..."
            @keyup.enter="muatDaftarBatch"
          />
          <button class="btn btn--ghost" @click="muatDaftarBatch">Cari</button>
        </div>
        <div class="ip-actions">
          <button class="btn btn--primary" @click="bukaFormBaru(JENIS.MIXING)">+ Batch Mixing</button>
          <button class="btn btn--secondary" @click="bukaFormBaru(JENIS.BLENDING)">+ Batch Blending</button>
        </div>
      </div>

      <div class="ip-table-wrap">
        <table class="ip-table">
          <thead>
            <tr>
              <th>Batch</th>
              <th>Tanggal</th>
              <th>Jenis</th>
              <th>Tangki Tujuan</th>
              <th>Nama Hasil</th>
              <th>Yield (Kg)</th>
              <th>Harga Rata</th>
              <th>Status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loadingList">
              <td colspan="9" class="ip-empty">Memuat data...</td>
            </tr>
            <tr v-else-if="daftarBatch.length === 0">
              <td colspan="9" class="ip-empty">Belum ada batch produksi.</td>
            </tr>
            <tr v-for="b in daftarBatch" :key="b.id">
              <td class="mono">{{ b.batch }}</td>
              <td>{{ formatTanggal(b.waktu || b.tanggal) }}</td>
              <td>{{ b.jenis === 'BLENDING' ? 'Blending' : 'Mixing' }}</td>
              <td>{{ b.tangki_tujuan_nama || b.tangki_tujuan }}</td>
              <td>{{ b.nama_hasil }}</td>
              <td class="num">{{ formatKg(b.qty_hasil) }}</td>
              <td class="num">{{ formatRupiah(b.harga_per_kg) }}</td>
              <td>
                <span class="status" :class="`status--${(b.status || 'draft').toLowerCase()}`">
                  {{ b.status || 'DRAFT' }}
                </span>
              </td>
              <td class="ip-row-actions">
                <button
                  v-if="(b.status || 'DRAFT') === 'DRAFT'"
                  class="btn btn--sm"
                  @click="bukaFormEdit(b.id)"
                >Ubah</button>
                <button
                  v-if="(b.status || 'DRAFT') === 'DRAFT'"
                  class="btn btn--sm btn--success"
                  :disabled="submitting"
                  @click="konfirmasiPosting(b)"
                >Posting</button>
                <button
                  v-if="(b.status || 'DRAFT') === 'DRAFT'"
                  class="btn btn--sm btn--danger"
                  :disabled="submitting"
                  @click="konfirmasiHapus(b)"
                >Hapus</button>
                <button
                  v-if="b.status === 'POSTED'"
                  class="btn btn--sm btn--danger"
                  :disabled="submitting"
                  @click="bukaModalVoid(b)"
                >Void</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- ================= MODE: FORM ================= -->
    <section v-else class="ip-form">
      <div class="ip-tabs" v-if="!editingBatchId">
        <button
          class="ip-tab"
          :class="{ 'ip-tab--active': jenisProduksi === JENIS.MIXING }"
          @click="gantiJenisProduksi(JENIS.MIXING)"
        >1. Mixing (Bahan Baku → Tangki)</button>
        <button
          class="ip-tab"
          :class="{ 'ip-tab--active': jenisProduksi === JENIS.BLENDING }"
          @click="gantiJenisProduksi(JENIS.BLENDING)"
        >2. Blending (WIP Tangki + Bahan Baku → Tangki)</button>
      </div>

      <div v-if="loadingForm" class="ip-empty">Memuat data...</div>

      <template v-else>
        <fieldset class="ip-panel">
          <legend>Telemetri Produksi</legend>
          <div class="ip-grid ip-grid--4">
            <label class="ip-field">
              <span>Nama Hasil</span>
              <input v-model="form.nama_hasil" type="text" placeholder="mis. Sabun Cair Lemon" />
            </label>

            <label class="ip-field">
              <span>Tangki Tujuan</span>
              <div class="ip-inline">
                <select v-model="form.tangki_tujuan">
                  <option value="" disabled>Pilih tangki</option>
                  <option v-for="t in daftarTangki" :key="t.id" :value="t.id">
                    {{ t.nama || t.kode }}
                  </option>
                </select>
                <button type="button" class="btn btn--icon" title="Tambah tangki baru" @click="tambahTangkiBaruPrompt">+</button>
              </div>
            </label>

            <label class="ip-field">
              <span>Batch ID</span>
              <div class="ip-inline">
                <input v-model="form.batch" type="text" placeholder="PRD-MIX-0001" />
                <button type="button" class="btn btn--icon" @click="generateNomorBatch">Auto</button>
              </div>
            </label>

            <label class="ip-field">
              <span>Tekor / Susut (Kg)</span>
              <input v-model.number="form.tekor_kg" type="number" step="0.001" min="0" />
            </label>
          </div>
        </fieldset>

        <fieldset v-if="jenisProduksi === JENIS.BLENDING" class="ip-panel">
          <legend>Alokasi WIP Sumber (Fluida Existing)</legend>
          <table class="ip-matrix">
            <thead>
              <tr>
                <th>Tangki Sumber</th>
                <th>Batch WIP</th>
                <th>Qty Transfer (Kg)</th>
                <th>Tersedia</th>
                <th>Harga WIP</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in wipRows" :key="row._id">
                <td>
                  <select v-model="row.tangki_asal" @change="saatTangkiAsalDipilih(row)">
                    <option value="" disabled>Pilih tangki</option>
                    <option v-for="t in daftarTangki" :key="t.id" :value="t.id">{{ t.nama || t.kode }}</option>
                  </select>
                </td>
                <td>
                  <select v-model="row.batch" :disabled="!row.tangki_asal" @change="saatBatchWipDipilih(row)">
                    <option value="" disabled>Pilih batch</option>
                    <option v-for="b in row.opsiBatch" :key="b.batch" :value="b.batch">{{ b.batch }}</option>
                  </select>
                </td>
                <td><input v-model.number="row.qty" type="number" step="0.001" min="0" /></td>
                <td class="num">{{ formatKg(row.tersedia) }}</td>
                <td class="num">{{ formatRupiah(row.harga) }}</td>
                <td><button type="button" class="btn btn--sm btn--danger" @click="hapusWipRow(row._id)">×</button></td>
              </tr>
            </tbody>
          </table>
          <button type="button" class="btn btn--ghost" @click="tambahWipRow">+ Tambah Sumber WIP</button>
        </fieldset>

        <fieldset class="ip-panel">
          <legend>{{ jenisProduksi === JENIS.BLENDING ? 'Bahan Baku Tambahan (BOM)' : 'Bill of Materials (BOM)' }}</legend>
          <table class="ip-matrix">
            <thead>
              <tr>
                <th>Bahan Baku</th>
                <th>Qty Terpakai (Kg)</th>
                <th>Saldo Pool</th>
                <th>Harga (IDR/Kg)</th>
                <th>Subtotal</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in bomRows" :key="row._id">
                <td>
                  <select v-model="row.raw" @change="perbaruiTelemetriBom(row)">
                    <option value="" disabled>Pilih bahan baku</option>
                    <option v-for="r in daftarRaw" :key="r.raw" :value="r.raw">{{ r.raw }}</option>
                  </select>
                </td>
                <td><input v-model.number="row.qty" type="number" step="0.001" min="0" /></td>
                <td class="num" :class="{ 'num--warn': row.qty > row.saldo }">{{ formatKg(row.saldo) }}</td>
                <td class="num">{{ formatRupiah(row.harga) }}</td>
                <td class="num">{{ formatRupiah(row.subtotal) }}</td>
                <td><button type="button" class="btn btn--sm btn--danger" @click="hapusBomRow(row._id)">×</button></td>
              </tr>
            </tbody>
          </table>
          <button type="button" class="btn btn--ghost" @click="tambahBomRow">+ Tambah Baris BOM</button>
        </fieldset>

        <div class="ip-projection">
          Proyeksi Yield: <strong>{{ formatKg(proyeksiYield) }} Kg</strong>
          &nbsp;|&nbsp;
          Estimasi Harga Pokok: <strong>{{ formatRupiah(proyeksiHargaRata) }} / Kg</strong>
        </div>

        <div v-if="pratinjau" class="ip-preview">
          <h3>Pratinjau Server</h3>
          <pre>{{ pratinjau }}</pre>
        </div>

        <div class="ip-form-actions">
          <button type="button" class="btn btn--ghost" @click="tutupForm" :disabled="submitting">Batal</button>
          <button type="button" class="btn btn--secondary" @click="mintaPratinjau" :disabled="submitting">Pratinjau</button>
          <button type="button" class="btn btn--primary" @click="simpanDraft" :disabled="submitting">
            {{ submitting ? 'Menyimpan...' : (editingBatchId ? 'Simpan Perubahan' : 'Simpan Draft') }}
          </button>
        </div>
      </template>
    </section>

    <!-- ================= MODAL VOID ================= -->
    <div v-if="modalVoid.tampil" class="ip-modal-backdrop" @click.self="tutupModalVoid">
      <div class="ip-modal">
        <h3>Void Batch {{ modalVoid.batch }}</h3>
        <label class="ip-field">
          <span>Alasan Void</span>
          <textarea v-model="modalVoid.alasan" rows="3" placeholder="Jelaskan alasan pembatalan batch..."></textarea>
        </label>
        <div class="ip-form-actions">
          <button class="btn btn--ghost" @click="tutupModalVoid">Batal</button>
          <button class="btn btn--danger" :disabled="submitting" @click="konfirmasiVoid">Konfirmasi Void</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
import { useInputProduksi } from './useInputProduksi'

const {
  JENIS,
  mode,
  jenisProduksi,
  editingBatchId,
  loadingList,
  loadingForm,
  submitting,
  errorMsg,
  daftarTangki,
  daftarRaw,
  daftarBatch,
  filter,
  form,
  bomRows,
  wipRows,
  pratinjau,

  proyeksiYield,
  proyeksiHargaRata,

  muatDaftarBatch,
  bukaFormBaru,
  bukaFormEdit,
  tutupForm,
  gantiJenisProduksi,
  tambahTangkiBaru,
  generateNomorBatch,
  tambahBomRow,
  hapusBomRow,
  perbaruiTelemetriBom,
  tambahWipRow,
  hapusWipRow,
  saatTangkiAsalDipilih,
  saatBatchWipDipilih,
  mintaPratinjau,
  simpanDraft,
  postingBatch,
  voidBatch,
  hapusDraft
} = useInputProduksi()

function formatKg(v) {
  return Number(v || 0).toLocaleString('id-ID', { minimumFractionDigits: 3, maximumFractionDigits: 3 })
}
function formatRupiah(v) {
  return `Rp ${Number(v || 0).toLocaleString('id-ID', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}
function formatTanggal(v) {
  if (!v) return '-'
  const d = new Date(v)
  return isNaN(d) ? v : d.toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' })
}

async function tambahTangkiBaruPrompt() {
  const nama = window.prompt('Nama/kode tangki baru:')
  if (!nama) return
  const dibuat = await tambahTangkiBaru(nama)
  if (dibuat) form.tangki_tujuan = dibuat.id
}

async function konfirmasiPosting(batch) {
  if (!window.confirm(`Posting batch ${batch.batch}? Aksi ini akan memotong saldo pool bahan baku.`)) return
  await postingBatch(batch.id)
}

async function konfirmasiHapus(batch) {
  if (!window.confirm(`Hapus draft batch ${batch.batch}?`)) return
  await hapusDraft(batch.id)
}

const modalVoid = reactive({ tampil: false, id: null, batch: '', alasan: '' })
function bukaModalVoid(batch) {
  modalVoid.tampil = true
  modalVoid.id = batch.id
  modalVoid.batch = batch.batch
  modalVoid.alasan = ''
}
function tutupModalVoid() {
  modalVoid.tampil = false
}
async function konfirmasiVoid() {
  const berhasil = await voidBatch(modalVoid.id, modalVoid.alasan)
  if (berhasil) tutupModalVoid()
}
</script>

<style scoped>
.input-produksi { max-width: 1200px; margin: 0 auto; padding: 24px; font-family: 'Segoe UI', sans-serif; color: #1f2933; }
.ip-header h1 { font-size: 20px; font-weight: 700; margin: 0; }
.ip-subtitle { color: #52606d; margin: 4px 0 0; }
.ip-alert { padding: 10px 14px; border-radius: 6px; margin: 12px 0; font-size: 14px; }
.ip-alert--error { background: #fde8e8; color: #c81e1e; border: 1px solid #f8b4b4; }

.ip-toolbar { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; margin: 16px 0; }
.ip-filter { display: flex; gap: 8px; flex-wrap: wrap; }
.ip-filter select, .ip-filter input { padding: 6px 10px; border: 1px solid #cbd2d9; border-radius: 6px; font-size: 13px; }
.ip-actions { display: flex; gap: 8px; }

.btn { padding: 7px 14px; border-radius: 6px; border: 1px solid transparent; font-size: 13px; cursor: pointer; background: #e4e7eb; color: #1f2933; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.btn--primary { background: #2563eb; color: #fff; }
.btn--secondary { background: #7c3aed; color: #fff; }
.btn--success { background: #16a34a; color: #fff; }
.btn--danger { background: #dc2626; color: #fff; }
.btn--ghost { background: transparent; border-color: #cbd2d9; }
.btn--icon { padding: 6px 10px; }
.btn--sm { padding: 4px 8px; font-size: 12px; margin-right: 4px; }

.ip-table-wrap { overflow-x: auto; border: 1px solid #e4e7eb; border-radius: 8px; }
.ip-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.ip-table th, .ip-table td { padding: 10px 12px; border-bottom: 1px solid #e4e7eb; text-align: left; white-space: nowrap; }
.ip-table th { background: #f5f7fa; font-weight: 600; }
.ip-empty { text-align: center; color: #9aa5b1; padding: 24px; }
.num { text-align: right; }
.num--warn { color: #dc2626; font-weight: 600; }
.mono { font-family: 'Consolas', monospace; }

.status { padding: 2px 8px; border-radius: 999px; font-size: 11px; font-weight: 600; text-transform: uppercase; }
.status--draft { background: #fef3c7; color: #92400e; }
.status--posted { background: #d1fae5; color: #065f46; }
.status--void { background: #fee2e2; color: #991b1b; }

.ip-row-actions { display: flex; }

.ip-tabs { display: flex; gap: 4px; margin-bottom: 16px; }
.ip-tab { padding: 10px 16px; border: 1px solid #cbd2d9; background: #f5f7fa; border-radius: 8px 8px 0 0; cursor: pointer; font-size: 13px; }
.ip-tab--active { background: #fff; border-bottom-color: #fff; font-weight: 700; color: #2563eb; }

.ip-panel { border: 1px solid #e4e7eb; border-radius: 8px; padding: 16px; margin-bottom: 16px; }
.ip-panel legend { font-weight: 600; padding: 0 6px; }

.ip-grid { display: grid; gap: 12px; }
.ip-grid--4 { grid-template-columns: repeat(4, 1fr); }
.ip-field { display: flex; flex-direction: column; gap: 4px; font-size: 13px; }
.ip-field input, .ip-field select, .ip-field textarea { padding: 7px 10px; border: 1px solid #cbd2d9; border-radius: 6px; font-size: 13px; }
.ip-inline { display: flex; gap: 6px; }
.ip-inline select { flex: 1; }

.ip-matrix { width: 100%; border-collapse: collapse; margin-bottom: 10px; }
.ip-matrix th, .ip-matrix td { padding: 6px 8px; font-size: 13px; }
.ip-matrix select, .ip-matrix input { width: 100%; padding: 6px 8px; border: 1px solid #cbd2d9; border-radius: 6px; }

.ip-projection { font-weight: 600; background: #eff6ff; color: #1d4ed8; padding: 10px 14px; border-radius: 8px; margin-bottom: 16px; }
.ip-preview { background: #f8fafc; border: 1px dashed #cbd2d9; padding: 12px; border-radius: 8px; margin-bottom: 16px; font-size: 12px; overflow-x: auto; }

.ip-form-actions { display: flex; justify-content: flex-end; gap: 8px; }

.ip-modal-backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 50; }
.ip-modal { background: #fff; border-radius: 10px; padding: 20px; width: 400px; max-width: 90vw; }
.ip-modal h3 { margin-top: 0; }
</style>
