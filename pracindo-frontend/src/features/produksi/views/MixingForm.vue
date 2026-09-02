<template>
  <div class="space-y-4">
    <div v-if="errorMsg" class="bg-red-50 text-red-600 border border-red-100 rounded-lg px-4 py-2.5 text-sm">
      {{ errorMsg }}
    </div>

    <div v-if="loadingForm" class="flex justify-center items-center py-10 text-slate-400">
      <i class="pi pi-spin pi-spinner text-3xl"></i>
    </div>

    <template v-else>
      <div class="bg-white rounded-xl border border-slate-200 shadow-sm p-4 w-full overflow-hidden">
        <h3 class="font-bold text-slate-800 text-sm mb-3 pb-2 border-b border-slate-100">Telemetri Produksi (Mixing)</h3>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
          <label class="flex flex-col gap-1 w-full overflow-hidden">
            <span class="text-[11px] font-bold text-slate-500 uppercase tracking-wide">Nama Hasil</span>
            <input v-model="form.nama_hasil" type="text" placeholder="mis. SUPER WHITE SPESIAL"
              class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors" />
          </label>

          <label class="flex flex-col gap-1 w-full overflow-hidden">
            <span class="text-[11px] font-bold text-slate-500 uppercase tracking-wide">Tangki Tujuan</span>
            <div class="flex items-center gap-2 w-full flex-nowrap">
              <select v-model="form.tangki_tujuan" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors" style="flex: 1 1 auto; min-width: 0;">
                <option value="" disabled>Pilih tangki</option>
                <option v-for="t in daftarTangki" :key="t.id" :value="t.id">{{ t.nama || t.kode }}</option>
              </select>
              <button type="button" class="bg-white border border-slate-200 hover:bg-slate-50 text-slate-600 rounded-lg flex items-center justify-center font-bold shadow-sm transition-colors" style="flex: 0 0 42px; width: 42px; height: 42px;" title="Tambah tangki baru" @click="tambahTangkiBaruPrompt">+</button>
            </div>
          </label>

          <label class="flex flex-col gap-1 w-full overflow-hidden">
            <span class="text-[11px] font-bold text-slate-500 uppercase tracking-wide">Batch ID</span>
            <div class="flex items-center gap-2 w-full flex-nowrap">
              <input v-model="form.batch" type="text" placeholder="PRD-MIX-0001" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors" style="flex: 1 1 auto; min-width: 0;" />
              <button type="button" class="bg-white border border-slate-200 hover:bg-slate-50 text-slate-600 text-xs font-bold rounded-lg flex items-center justify-center shadow-sm transition-colors" style="flex: 0 0 65px; width: 65px; height: 42px;" @click="generateNomorBatch">Auto</button>
            </div>
          </label>

          <label class="flex flex-col gap-1 w-full overflow-hidden">
            <span class="text-[11px] font-bold text-slate-500 uppercase tracking-wide">Tekor / Susut (Kg)</span>
            <input v-model.number="form.tekor_kg" type="number" step="0.001" min="0" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors" />
          </label>
        </div>
      </div>

      <div class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden w-full">
        <div class="p-4 pb-3">
          <h3 class="font-bold text-slate-800 text-sm">Bill of Materials (BOM)</h3>
        </div>

        <div class="overflow-x-auto border-y border-slate-100">
          <table class="w-full text-sm text-left whitespace-nowrap">
            <thead class="bg-slate-50 text-slate-500 text-[11px] uppercase font-semibold">
              <tr>
                <th class="px-4 py-2">Bahan Baku</th>
                <th class="px-4 py-2">Qty Terpakai (Kg)</th>
                <th class="px-4 py-2 text-right">Saldo Pool</th>
                <th class="px-4 py-2 text-right">Harga (IDR/Kg)</th>
                <th class="px-4 py-2 text-right">Subtotal</th>
                <th class="px-4 py-2 text-center">Aksi</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 text-sm">
              <tr v-for="row in bomRows" :key="row._id" class="hover:bg-slate-50/50 transition-colors">
                <td class="px-4 py-2">
                  <select v-model="row.raw" @change="perbaruiTelemetriBom(row); cekBahanDuplikat(row)" class="w-full min-w-[180px] px-2 py-1.5 bg-slate-50 border border-slate-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20">
                    <option value="" disabled>Pilih bahan baku</option>
                      <option 
                        v-for="r in daftarRaw" 
                        :key="r.raw" 
                        :value="r.raw"
                        :disabled="bomRows.some(b => b.raw === r.raw && b._id !== row._id)"
                      >
                        {{ r.produk_kode }} - {{ r.produk_nama }} ({{ formatKg(r.qty_kg) }} Kg)
                      </option>
                  </select>
                </td>
                <td class="px-4 py-2">
                  <input v-model.number="row.qty" type="number" step="0.001" min="0" class="w-full min-w-[100px] px-2 py-1.5 bg-white border border-slate-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20" />
                </td>
                <td class="px-4 py-2 text-right">
                  <span class="font-medium" :class="row.qty > row.saldo ? 'text-red-600' : 'text-slate-700'">
                    {{ formatKg(row.saldo) }}
                  </span>
                </td>
                <td class="px-4 py-2 text-right text-slate-500">{{ formatRupiah(row.harga) }}</td>
                <td class="px-4 py-2 text-right font-semibold text-slate-700">{{ formatRupiah(row.subtotal) }}</td>
                <td class="px-4 py-2 text-center">
                  <button type="button" class="w-7 h-7 rounded-md flex items-center justify-center text-red-400 hover:bg-red-50 hover:text-red-600 mx-auto transition-colors" @click="hapusBomRow(row._id)">
                    <i class="pi pi-trash text-xs"></i>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="p-3 bg-slate-50/50">
          <button type="button" class="text-xs font-bold text-blue-600 bg-blue-50 hover:bg-blue-100 px-3 py-1.5 rounded-lg transition-colors flex items-center gap-2" @click="tambahBomRow">
            <i class="pi pi-plus text-[10px]"></i> Tambah Baris BOM
          </button>
        </div>
      </div>

      <div class="bg-blue-50 border border-blue-100 rounded-xl p-4 flex flex-col sm:flex-row justify-between items-center gap-2 text-sm text-center sm:text-left">
        <div class="text-blue-800">
          Proyeksi Yield: <strong class="text-blue-900 ml-1">{{ formatKg(proyeksiYield) }} Kg</strong>
        </div>
        <div class="text-blue-800">
          Estimasi Cost Nom: <strong class="text-blue-900 ml-1">{{ formatRupiah(proyeksiHargaRata) }} / Kg</strong>
        </div>
      </div>

      <div v-if="pratinjau" class="mb-3">
        <PratinjauValuasi :hasil="pratinjau" />
      </div>

      <div class="flex flex-col sm:flex-row justify-end gap-2.5 pt-3 border-t border-slate-100">
        <button type="button" class="px-4 py-2 text-sm font-bold text-slate-600 bg-white border border-slate-200 hover:bg-slate-50 rounded-lg transition-all disabled:opacity-50" @click="$emit('batal')" :disabled="submitting">Batal</button>
        <button type="button" class="px-4 py-2 text-sm font-bold text-blue-700 bg-blue-50 border border-blue-100 hover:bg-blue-100 rounded-lg transition-all disabled:opacity-50" @click="mintaPratinjau" :disabled="submitting">Pratinjau</button>
        <button type="button" class="px-5 py-2 text-sm font-bold text-white bg-emerald-600 hover:bg-emerald-700 rounded-lg shadow-sm transition-all disabled:opacity-50" @click="tanganiSimpanDanPosting" :disabled="submitting">
          {{ submitting ? 'Memproses...' : 'Simpan & Posting' }}
        </button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useMixingForm } from '../composables/useMixingForm' 
import PratinjauValuasi from '../components/PratinjauValuasi.vue'

const props = defineProps({
  batchId: { type: [String, Number], default: null }
})

const emit = defineEmits(['batal', 'sukses'])

const {
  loadingForm,
  submitting,
  errorMsg,
  daftarTangki,
  daftarRaw,
  form,
  bomRows,
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
  mintaPratinjau,
  simpanDanPosting
} = useMixingForm()

onMounted(() => {
  if (props.batchId) {
    bukaFormEdit(props.batchId)
  } else {
    bukaFormBaru()
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

async function tanganiSimpanDanPosting() {
  const ok = await simpanDanPosting(props.batchId)
  if (ok) emit('sukses')
}

const cekBahanDuplikat = (row) => {
  if (!row.raw) return;
  const jumlahMuncul = bomRows.value.filter(r => r.raw === row.raw).length;
  if (jumlahMuncul > 1) {
    alert('Bahan baku ini sudah dipilih di baris BOM lain! Silakan gabungkan QTY-nya.');
    row.raw = ""; 
    perbaruiTelemetriBom(row); 
  }
}
</script>