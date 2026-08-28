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
                  @click="bukaFormEdit(b)"
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

    <!-- FORM MODE -->
    <section v-else class="ip-form">
      <div class="ip-tabs" v-if="!editingBatchId">
        <button
          class="ip-tab"
          :class="{ 'ip-tab--active': jenisProduksi === JENIS.MIXING }"
          @click="jenisProduksi = JENIS.MIXING"
        >1. Mixing (Bahan Baku &rarr; Tangki)</button>
        <button
          class="ip-tab"
          :class="{ 'ip-tab--active': jenisProduksi === JENIS.BLENDING }"
          @click="jenisProduksi = JENIS.BLENDING"
        >2. Blending (WIP Tangki + Bahan Baku &rarr; Tangki)</button>
      </div>

      <!-- Render Formulir Sesuai Jenis -->
      <MixingForm
        v-if="jenisProduksi === JENIS.MIXING"
        :batch-id="editingBatchId"
        @batal="tutupForm"
        @sukses="saatFormSukses"
      />

      <BlendingForm
        v-else-if="jenisProduksi === JENIS.BLENDING"
        :batch-id="editingBatchId"
        @batal="tutupForm"
        @sukses="saatFormSukses"
      />
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
import { ref, reactive } from 'vue'
import { useInputProduksi } from '../composables/useInputProduksi'
import MixingForm from './MixingForm.vue'
import BlendingForm from './BlendingForm.vue'

const {
  JENIS,
  loadingList,
  submitting,
  errorMsg,
  daftarBatch,
  filter,
  muatDaftarBatch,
  postingBatch,
  voidBatch,
  hapusDraft
} = useInputProduksi()

const mode = ref('list')
const jenisProduksi = ref(JENIS.MIXING)
const editingBatchId = ref(null)

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

function bukaFormBaru(jenis) {
  jenisProduksi.value = jenis
  editingBatchId.value = null
  mode.value = 'form'
}

function bukaFormEdit(batch) {
  jenisProduksi.value = batch.jenis || JENIS.MIXING
  editingBatchId.value = batch.id
  mode.value = 'form'
}

function tutupForm() {
  mode.value = 'list'
  editingBatchId.value = null
}

async function saatFormSukses() {
  tutupForm()
  await muatDaftarBatch()
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
/* Styling tetap konsisten */
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

.ip-modal-backdrop { position: fixed; inset: 0; background: rgba(26,34,51,0.45); backdrop-filter: blur(2px); display: flex; align-items: center; justify-content: center; z-index: 50; padding: var(--space-md); }
.ip-modal { background: var(--bg-card); border-radius: var(--radius-lg); padding: var(--space-lg); width: 420px; max-width: 100%; box-shadow: 0 20px 60px rgba(17,24,39,0.25); }
.ip-modal h3 { margin-top: 0; color: var(--text-primary); }

.mt-4 { margin-top: 1rem; }
.mb-4 { margin-bottom: 1rem; }

@media (max-width: 768px) {
  .input-produksi { padding: var(--space-md); }
  .ip-toolbar { flex-direction: column; align-items: stretch; }
  .ip-filter { flex-direction: column; }
  .ip-actions { flex-direction: column; }
  .ip-actions .btn { width: 100%; }
  .ip-modal { width: 100%; }
}
@media (max-width: 480px) { .ip-header h1 { font-size: 1.25rem; } }
</style>
