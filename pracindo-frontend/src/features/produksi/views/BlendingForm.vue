<template>
  <div class="blending-form">
    <p v-if="errorMsg" class="ip-alert ip-alert--error">{{ errorMsg }}</p>

    <div v-if="loadingForm" class="ip-empty">Memuat data blending...</div>
    <template v-else>
      <!-- Telemetri Produksi -->
      <fieldset class="ip-panel">
        <legend>Telemetri Produksi (Blending)</legend>
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
              <input v-model="form.batch" type="text" placeholder="PRD-BLD-0001" />
              <button type="button" class="btn btn--icon" @click="generateNomorBatch">Auto</button>
            </div>
          </label>
          <label class="ip-field">
            <span>Tekor / Susut (Kg)</span>
            <input v-model.number="form.tekor_kg" type="number" step="0.001" min="0" />
          </label>
        </div>
      </fieldset>

      <!-- Alokasi WIP Sumber (Fluida Existing) -->
      <fieldset class="ip-panel">
        <legend>Alokasi WIP Sumber (Fluida Existing)</legend>

        <div class="ip-resp-table">
          <div class="ip-resp-thead grid-wip">
            <div>Tangki Sumber</div>
            <div>Batch WIP</div>
            <div>Qty Transfer (Kg)</div>
            <div class="text-right">Tersedia</div>
            <div class="text-right">Harga WIP</div>
            <div></div>
          </div>

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

      <!-- Bahan Baku Tambahan (BOM) -->
      <fieldset class="ip-panel">
        <legend>Bahan Baku Tambahan (BOM)</legend>

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

      <!-- Proyeksi Yield & Valuasi -->
      <div class="ip-projection">
        Proyeksi Yield: <strong>{{ formatKg(proyeksiYield) }} Kg</strong>
        &nbsp;|&nbsp;
        Estimasi Harga Pokok: <strong>{{ formatRupiah(proyeksiHargaRata) }} / Kg</strong>
      </div>

      <div class="mb-4">
        <PratinjauValuasi v-if="pratinjau" :hasil="pratinjau" />
      </div>

      <!-- Actions -->
      <div class="ip-form-actions">
        <button type="button" class="btn btn--ghost" @click="$emit('batal')" :disabled="submitting">Batal</button>
        <button type="button" class="btn btn--secondary" @click="mintaPratinjau" :disabled="submitting">Pratinjau</button>
        <button type="button" class="btn btn--primary" @click="tanganiSimpanDraft" :disabled="submitting">
          {{ submitting ? 'Menyimpan...' : (batchId ? 'Simpan Perubahan' : 'Simpan Draft') }}
        </button>
        <button type="button" class="btn btn--success" @click="tanganiSimpanDanPosting" :disabled="submitting">
          Simpan &amp; Posting
        </button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useInputProduksi } from '../composables/useInputProduksi'
import PratinjauValuasi from '../components/PratinjauValuasi.vue'

const props = defineProps({
  batchId: { type: [String, Number], default: null }
})

const emit = defineEmits(['batal', 'sukses'])

const {
  JENIS,
  loadingForm,
  submitting,
  errorMsg,
  daftarTangki,
  daftarRaw,
  form,
  bomRows,
  wipRows,
  pratinjau,
  proyeksiYield,
  proyeksiHargaRata,
  bukaFormBaru,
  bukaFormEdit,
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
  simpanDanPosting
} = useInputProduksi()

onMounted(() => {
  if (props.batchId) {
    bukaFormEdit(props.batchId)
  } else {
    bukaFormBaru(JENIS.BLENDING)
  }
})

function formatKg(v) {
  return Number(v || 0).toLocaleString('id-ID', { minimumFractionDigits: 3, maximumFractionDigits: 3 })
}

function formatRupiah(v) {
  return `Rp ${Number(v || 0).toLocaleString('id-ID', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

async function tambahTangkiBaruPrompt() {
  const nama = window.prompt('Nama/kode tangki baru:')
  if (!nama) return
  const dibuat = await tambahTangkiBaru(nama)
  if (dibuat) form.tangki_tujuan = dibuat.id
}

async function tanganiSimpanDraft() {
  const ok = await simpanDraft()
  if (ok) emit('sukses')
}

async function tanganiSimpanDanPosting() {
  const ok = await simpanDanPosting()
  if (ok) emit('sukses')
}
</script>
