<template>
  <div class="input-produksi">
    <header class="ip-header">
      <h1>Modul Produksi (Mixing &amp; Blending)</h1>
      <p v-if="mode === 'form'" class="ip-subtitle">
        {{ editingBatchId ? 'Ubah Draft Batch' : 'Buat Batch Baru' }}
        {{ jenisProduksi === JENIS.MIXING ? 'Mixing' : 'Blending' }}
      </p>
    </header>

    <p v-if="errorMsg" class="ip-alert ip-alert--error">{{ errorMsg }}</p>

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
              <td class="num">{{ formatRupiah(b.harga_per_kg || b.harga_rata) }}</td>
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

    <section v-else class="ip-form">
      <div class="ip-tabs" v-if="!editingBatchId">
        <button
          class="ip-tab"
          :class="{ 'ip-tab--active': jenisProduksi === JENIS.MIXING }"
          @click="gantiJenisProduksi(JENIS.MIXING)"
        >1. Mixing (Bahan Baku &rarr; Tangki)</button>
        <button
          class="ip-tab"
          :class="{ 'ip-tab--active': jenisProduksi === JENIS.BLENDING }"
          @click="gantiJenisProduksi(JENIS.BLENDING)"
        >2. Blending (WIP Tangki + Bahan Baku &rarr; Tangki)</button>
      </div>

      <div v-if="loadingForm" class="ip-empty">Memuat data...</div>
      <template v-else>
        <fieldset class="ip-panel">
          <legend>Telemetri Produksi</legend>
          <div class="ip-grid ip-grid--4">
            <label class="ip-field">
              <span>Nama Hasil</span>
              <input v-model="form.nama_hasil" type="text" placeholder="mis. SUPER WHITE SPESIAL" />
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

          <div class="ip-resp-table">
            <!-- Header Desktop -->
            <div class="ip-resp-thead grid-wip">
              <div>Tangki Sumber</div>
              <div>Batch WIP</div>
              <div>Qty Transfer (Kg)</div>
              <div class="text-right">Tersedia</div>
              <div class="text-right">Harga WIP</div>
              <div></div>
            </div>

            <!-- Body Rows -->
            <div class="ip-resp-tbody">
              <div class="ip-resp-tr grid-wip" v-for="row in wipRows" :key="row._id">
                <div class="ip-resp-td">
                  <label class="ip-resp-label">Tangki Sumber</label>
                  <select v-model="row.tangki_asal" @change="saatTangkiAsalDipilih(row)">
                    <option value="" disabled>Pilih tangki</option>
                    <option v-for="t in daftarTangki" :key="t.id" :value="t.id">{{ t.nama || t.kode }}</option>
                  </select>
                </div>

                <div class="ip-resp-td">
                  <label class="ip-resp-label">Batch WIP</label>
                  <select v-model="row.batch" :disabled="!row.tangki_asal" @change="saatBatchWipDipilih(row)">
                    <option value="" disabled>Pilih batch</option>
                    <option v-for="b in row.opsiBatch" :key="b.batch" :value="b.batch">{{ b.batch }}</option>
                  </select>
                </div>

                <div class="ip-resp-td">
                  <label class="ip-resp-label">Qty Transfer (Kg)</label>
                  <input v-model.number="row.qty" type="number" step="0.001" min="0" />
                </div>

                <div class="ip-resp-td md-align-right justify-center">
                  <label class="ip-resp-label">Tersedia</label>
                  <span class="num">{{ formatKg(row.tersedia) }}</span>
                </div>

                <div class="ip-resp-td md-align-right justify-center">
                  <label class="ip-resp-label">Harga WIP</label>
                  <span class="num">{{ formatRupiah(row.harga) }}</span>
                </div>

                <div class="ip-resp-td justify-center">
                  <button type="button" class="btn btn--sm btn--danger w-full-hp" @click="hapusWipRow(row._id)">Hapus</button>
                </div>
              </div>
            </div>
          </div>

          <button type="button" class="btn btn--ghost mt-4" @click="tambahWipRow">+ Tambah Sumber WIP</button>
        </fieldset>

        <fieldset class="ip-panel">
          <legend>{{ jenisProduksi === JENIS.BLENDING ? 'Bahan Baku Tambahan (BOM)' : 'Bill of Materials (BOM)' }}</legend>

          <div class="ip-resp-table">
            <div class="ip-resp-thead grid-bom">
              <div>Bahan Baku</div>
              <div>Qty Terpakai (Kg)</div>
              <div class="text-right">Saldo Pool</div>
              <div class="text-right">Harga (IDR/Kg)</div>
              <div class="text-right">Subtotal</div>
              <div></div>
            </div>

            <div class="ip-resp-tbody">
              <div class="ip-resp-tr grid-bom" v-for="row in bomRows" :key="row._id">
                <div class="ip-resp-td">
                  <label class="ip-resp-label">Bahan Baku</label>
                  <select v-model="row.raw" @change="perbaruiTelemetriBom(row)">
                    <option value="" disabled>Pilih bahan baku</option>
                    <option v-for="r in daftarRaw" :key="r.raw" :value="r.raw">
                      {{ r.produk_kode }} - {{ r.produk_nama }} ({{ formatKg(r.qty_kg) }} Kg)
                    </option>
                  </select>
                </div>

                <div class="ip-resp-td">
                  <label class="ip-resp-label">Qty Terpakai (Kg)</label>
                  <input v-model.number="row.qty" type="number" step="0.001" min="0" />
                </div>

                <div class="ip-resp-td md-align-right justify-center">
                  <label class="ip-resp-label">Saldo Pool</label>
                  <span class="num" :class="{ 'num--warn': row.qty > row.saldo }">{{ formatKg(row.saldo) }}</span>
                </div>

                <div class="ip-resp-td md-align-right justify-center">
                  <label class="ip-resp-label">Harga (IDR/Kg)</label>
                  <span class="num">{{ formatRupiah(row.harga) }}</span>
                </div>

                <div class="ip-resp-td md-align-right justify-center">
                  <label class="ip-resp-label">Subtotal</label>
                  <span class="num">{{ formatRupiah(row.subtotal) }}</span>
                </div>

                <div class="ip-resp-td justify-center">
                  <button type="button" class="btn btn--sm btn--danger w-full-hp" @click="hapusBomRow(row._id)">Hapus</button>
                </div>
              </div>
            </div>
          </div>

          <button type="button" class="btn btn--ghost mt-4" @click="tambahBomRow">+ Tambah Baris BOM</button>
        </fieldset>

        <div class="ip-projection">
          Proyeksi Yield: <strong>{{ formatKg(proyeksiYield) }} Kg</strong>
          &nbsp;|&nbsp;
          Estimasi Harga Pokok: <strong>{{ formatRupiah(proyeksiHargaRata) }} / Kg</strong>
        </div>

        <div class="mb-4">
          <PratinjauValuasi v-if="pratinjau" :hasil="pratinjau" />
        </div>

        <div class="ip-form-actions">
          <button type="button" class="btn btn--ghost" @click="tutupForm" :disabled="submitting">Batal</button>
          <button type="button" class="btn btn--secondary" @click="mintaPratinjau" :disabled="submitting">Pratinjau</button>
          <button type="button" class="btn btn--primary" @click="simpanDraft" :disabled="submitting">
            {{ submitting ? 'Menyimpan...' : (editingBatchId ? 'Simpan Perubahan' : 'Simpan Draft') }}
          </button>
          <button type="button" class="btn btn--success" @click="simpanDanPosting" :disabled="submitting">
            Simpan &amp; Posting
          </button>
        </div>
      </template>
    </section>

    <div v-if="modalVoid.tampil" class="ip-modal-backdrop" @click.self="tutupModalVoid">
      <div class="ip-modal">
        <h3>Void Batch {{ modalVoid.batch }}</h3>
        <label class="ip-field">
          <span>Alasan Void</span>
          <textarea v-model="modalVoid.alasan" rows="3" placeholder="Jelaskan alasan pembatalan batch..."></textarea>
        </label>
        <div class="ip-form-actions mt-4">
          <button class="btn btn--ghost" @click="tutupModalVoid">Batal</button>
          <button class="btn btn--danger" :disabled="submitting" @click="konfirmasiVoid">Konfirmasi Void</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
import { useInputProduksi } from '../composables/useInputProduksi'
import PratinjauValuasi from '../components/PratinjauValuasi.vue'

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
  simpanDanPosting,
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
.input-produksi { max-width: 1280px; margin: 0 auto; padding: var(--space-lg); font-family: var(--font-sans); color: var(--text-primary); }

.ip-header { margin-bottom: var(--space-md); }
.ip-header h1 { font-size: clamp(1.4rem, 1.1rem + 1vw, 1.9rem); font-weight: 800; margin: 0; color: var(--text-primary); }
.ip-subtitle { color: var(--text-secondary); margin: 4px 0 0; font-size: 0.9rem; }

.ip-alert { padding: 0.8rem 1.1rem; border-radius: var(--radius-md); margin: var(--space-md) 0; font-size: 0.875rem; }
.ip-alert--error { background: var(--danger-soft); color: #DC2626; }

.ip-toolbar { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: var(--space-md); margin: var(--space-md) 0 var(--space-lg); }
.ip-filter { display: flex; gap: var(--space-sm); flex-wrap: wrap; flex: 1; min-width: 0; }
.ip-filter select, .ip-filter input {
  padding: 0.6rem 0.9rem; border: 1.5px solid var(--border-color); background: var(--bg-input);
  color: var(--text-primary); border-radius: var(--radius-md); font-size: 0.85rem; min-height: 42px; transition: all var(--transition);
}
.ip-filter select:focus, .ip-filter input:focus { outline: none; background: var(--bg-card); border-color: var(--primary); box-shadow: var(--ring-focus); }
.ip-filter input::placeholder { color: var(--text-muted); }
.ip-actions { display: flex; gap: var(--space-sm); flex-wrap: wrap; }

.btn {
  padding: 0.6rem 1.15rem; border-radius: var(--radius-full); border: 1px solid var(--border-color);
  font-size: 0.85rem; font-weight: 700; cursor: pointer; background: var(--bg-card); color: var(--text-primary);
  transition: all var(--transition); white-space: nowrap;
}
.btn:hover { background: var(--bg-input); }
.btn:active { transform: scale(0.98); }
.btn:disabled { opacity: 0.45; cursor: not-allowed; transform: none; }

.btn--primary { background: var(--primary); border: none; color: #fff; box-shadow: var(--shadow-btn); }
.btn--primary:hover { background: var(--primary-dark); }

.btn--secondary { background: var(--primary-soft); border-color: transparent; color: var(--primary-dark); }
.btn--secondary:hover { background: var(--primary-light); }

.btn--success { background: var(--success-soft); border-color: transparent; color: #15803D; }
.btn--success:hover { background: #D3F3DD; }

.btn--danger { background: var(--danger-soft); border-color: transparent; color: #DC2626; }
.btn--danger:hover { background: #FBD5D5; }

.btn--ghost { background: transparent; border-color: var(--border-color); color: var(--text-secondary); }
.btn--ghost:hover { background: var(--bg-input); color: var(--text-primary); }

.btn--icon { padding: 0.6rem 0.75rem; border-radius: var(--radius-md); }
.btn--sm { padding: 0.35rem 0.7rem; font-size: 0.75rem; margin-right: 4px; border-radius: var(--radius-full); }

.ip-table-wrap { overflow-x: auto; border: 1px solid var(--border-color); border-radius: var(--radius-lg); background: var(--bg-card); box-shadow: var(--shadow-card); }
.ip-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
.ip-table th, .ip-table td { padding: 0.85rem 1rem; border-bottom: 1px solid var(--border-color); text-align: left; white-space: nowrap; }
.ip-table th { background: var(--bg-input); color: var(--text-secondary); font-weight: 700; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.05em; }
.ip-table tbody tr { transition: background var(--transition); }
.ip-table tbody tr:hover { background: var(--bg-input); }
.ip-table tbody tr:last-child td { border-bottom: none; }
.ip-empty { text-align: center; color: var(--text-muted); padding: var(--space-xl); }
.num { text-align: right; font-family: var(--font-mono); }
.num--warn { color: #DC2626; font-weight: 700; }
.mono { font-family: var(--font-mono); }

.status { display: inline-flex; align-items: center; padding: 0.25rem 0.75rem; border-radius: var(--radius-full); font-size: 0.68rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.04em; }
.status--draft { background: var(--warning-soft); color: #B45309; }
.status--posted { background: var(--success-soft); color: #15803D; }
.status--void { background: var(--danger-soft); color: #DC2626; }

.ip-row-actions { display: flex; flex-wrap: wrap; gap: 4px; }

.ip-tabs { display: flex; gap: var(--space-sm); margin-bottom: var(--space-md); overflow-x: auto; }
.ip-tab {
  padding: 0.7rem 1.1rem; border: 1.5px solid var(--border-color); background: var(--bg-card);
  color: var(--text-secondary); border-radius: var(--radius-full); cursor: pointer;
  font-size: 0.82rem; font-weight: 700; white-space: nowrap; transition: all var(--transition);
}
.ip-tab:hover { border-color: var(--border-strong); }
.ip-tab--active { background: var(--primary); border-color: var(--primary); color: #fff; box-shadow: var(--shadow-btn); }

.ip-panel { border: 1px solid var(--border-color); border-radius: var(--radius-lg); padding: var(--space-lg); margin-bottom: var(--space-lg); background: var(--bg-card); box-shadow: var(--shadow-card); }
.ip-panel legend { font-weight: 800; padding: 0 8px; color: var(--text-primary); font-size: 0.88rem; }

.ip-grid { display: grid; gap: var(--space-md); }
.ip-grid--4 { grid-template-columns: repeat(4, 1fr); }

.ip-field { display: flex; flex-direction: column; gap: 4px; font-size: 0.85rem; }
.ip-field span { color: var(--text-secondary); font-weight: 600; }
.ip-field input, .ip-field select, .ip-field textarea {
  padding: 0.6rem 0.9rem; border: 1.5px solid var(--border-color); background: var(--bg-input);
  color: var(--text-primary); border-radius: var(--radius-md); font-size: 0.85rem; transition: all var(--transition);
}
.ip-field input:focus, .ip-field select:focus, .ip-field textarea:focus { outline: none; background: var(--bg-card); border-color: var(--primary); box-shadow: var(--ring-focus); }
.ip-inline { display: flex; gap: 6px; }
.ip-inline select { flex: 1; min-width: 0; }

.ip-projection {
  font-weight: 700; background: var(--primary-soft); border: 1px solid var(--primary-light);
  color: var(--text-primary); padding: 0.85rem 1.1rem; border-radius: var(--radius-md); margin-bottom: var(--space-lg); font-size: 0.9rem;
}
.ip-projection strong { color: var(--primary-dark); font-family: var(--font-mono); }

.ip-form-actions { display: flex; justify-content: flex-end; gap: var(--space-sm); flex-wrap: wrap; }

.ip-modal-backdrop { position: fixed; inset: 0; background: rgba(26,34,51,0.45); backdrop-filter: blur(2px); display: flex; align-items: center; justify-content: center; z-index: 50; padding: var(--space-md); }
.ip-modal { background: var(--bg-card); border-radius: var(--radius-lg); padding: var(--space-lg); width: 420px; max-width: 100%; box-shadow: 0 20px 60px rgba(17,24,39,0.25); }
.ip-modal h3 { margin-top: 0; color: var(--text-primary); }

.mt-4 { margin-top: 1rem; }
.mb-4 { margin-bottom: 1rem; }

/* --- GAYA TABEL RESPONSIF (KARTU DI HP, TABEL DI DESKTOP) --- */
.ip-resp-table { display: flex; flex-direction: column; gap: 1rem; }
.ip-resp-thead { display: none; }

.ip-resp-tr {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
  background: var(--bg-input);
  padding: 1.25rem;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
}
.ip-resp-td { display: flex; flex-direction: column; gap: 6px; justify-content: center; }
.ip-resp-label { font-size: 0.72rem; font-weight: 800; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.05em; }
.ip-resp-td select, .ip-resp-td input { width: 100%; padding: 0.6rem 0.9rem; border: 1.5px solid var(--border-color); background: var(--bg-card); color: var(--text-primary); border-radius: var(--radius-md); font-size: 0.85rem; }
.ip-resp-td select:focus, .ip-resp-td input:focus { outline: none; border-color: var(--primary); box-shadow: var(--ring-focus); }
.w-full-hp { width: 100%; padding: 0.6rem; margin-top: 0.5rem; }
.text-right { text-align: left; }

@media (min-width: 768px) {
  .ip-resp-table { gap: 0; }

  .ip-resp-thead {
    display: grid;
    padding: 0.75rem 1rem;
    font-size: 0.72rem;
    font-weight: 800;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    border-bottom: 2px solid var(--border-color);
  }

  .ip-resp-tr {
    display: grid;
    background: transparent;
    padding: 0.75rem 1rem;
    border: none;
    border-bottom: 1px solid var(--border-color);
    border-radius: 0;
    align-items: center;
    gap: 1rem;
  }
  .ip-resp-tr:hover { background: var(--bg-input); }

  .ip-resp-label { display: none; }

  .w-full-hp { width: auto; margin-top: 0; }
  .text-right { text-align: right; }
  .md-align-right { align-items: flex-end; }

  .grid-wip { grid-template-columns: 2fr 2fr 1.5fr 1fr 1fr 60px; gap: 1rem; }
  .grid-bom { grid-template-columns: 2.5fr 1.5fr 1fr 1.5fr 1.5fr 60px; gap: 1rem; }
}

@media (max-width: 1024px) { .ip-grid--4 { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 768px) {
  .input-produksi { padding: var(--space-md); }
  .ip-toolbar { flex-direction: column; align-items: stretch; }
  .ip-filter { flex-direction: column; }
  .ip-actions { flex-direction: column; }
  .ip-actions .btn { width: 100%; }
  .ip-grid--4 { grid-template-columns: 1fr; }
  .ip-form-actions { flex-direction: column-reverse; }
  .ip-form-actions .btn { width: 100%; }
  .ip-modal { width: 100%; }
}
@media (max-width: 480px) { .ip-header h1 { font-size: 1.25rem; } }
</style>
