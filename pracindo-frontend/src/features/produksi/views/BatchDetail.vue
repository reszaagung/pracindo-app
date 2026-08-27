<template>
  <div class="space-y-6">
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div class="flex items-center gap-3">
        <button
          @click="router.back()"
          class="w-9 h-9 flex-shrink-0 bg-slate-900 rounded-xl flex items-center justify-center shadow-md active:scale-95 transition-transform"
        >
          <i class="pi pi-arrow-left text-white text-sm"></i>
        </button>
        <div>
          <h1 class="text-xl md:text-2xl font-bold text-slate-800">Detail Batch</h1>
          <p class="text-sm text-slate-500 mt-1 font-mono">{{ batch?.batch || batch?.nomor || 'Memuat...' }}</p>
        </div>
      </div>
      <span
        v-if="batch"
        class="inline-flex items-center px-3 py-1.5 rounded-full text-sm font-semibold border"
        :class="{
          'bg-amber-50 text-amber-700 border-amber-200': batch.status === 'DRAFT',
          'bg-emerald-50 text-emerald-700 border-emerald-200': batch.status === 'POSTED',
          'bg-red-50 text-red-700 border-red-200': batch.status === 'VOID'
        }"
      >
        {{ batch.status }}
      </span>
    </div>

    <div v-if="errorMsg" class="bg-red-50 text-red-600 border border-red-100 rounded-xl px-4 py-3 text-sm">
      {{ errorMsg }}
    </div>

    <div v-if="loading" class="flex justify-center items-center py-20 text-slate-400">
      <i class="pi pi-spin pi-spinner text-3xl"></i>
    </div>

    <template v-else-if="batch">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div class="bg-white rounded-2xl border border-slate-100 shadow-[0_4px_20px_rgb(0,0,0,0.03)] p-5">
          <h3 class="font-bold text-slate-800 mb-4 flex items-center gap-2">
            <i class="pi pi-info-circle text-blue-500"></i> Informasi Utama
          </h3>
          <div class="space-y-3 text-sm">
            <div class="flex justify-between border-b border-slate-50 pb-2">
              <span class="text-slate-500">Nama Hasil</span>
              <span class="font-semibold text-slate-800">{{ batch.nama_hasil }}</span>
            </div>
            <div class="flex justify-between border-b border-slate-50 pb-2">
              <span class="text-slate-500">Jenis Proses</span>
              <span class="font-semibold text-slate-800">{{ batch.jenis }}</span>
            </div>
            <div class="flex justify-between border-b border-slate-50 pb-2">
              <span class="text-slate-500">Tangki Tujuan</span>
              <span class="font-semibold text-slate-800">{{ batch.tangki_tujuan_nama || batch.tangki_kode || batch.tangki }}</span>
            </div>
            <div class="flex justify-between pb-1">
              <span class="text-slate-500">Waktu Transaksi</span>
              <span class="font-semibold text-slate-800">{{ formatTanggal(batch.waktu || batch.created_at) }}</span>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-2xl border border-slate-100 shadow-[0_4px_20px_rgb(0,0,0,0.03)] p-5">
          <h3 class="font-bold text-slate-800 mb-4 flex items-center gap-2">
            <i class="pi pi-chart-bar text-purple-500"></i> Telemetri Nilai & Kuantitas
          </h3>
          <div class="space-y-3 text-sm">
            <div class="flex justify-between border-b border-slate-50 pb-2">
              <span class="text-slate-500">Total Input Massa</span>
              <span class="font-semibold text-slate-800">{{ formatKg(batch.total_qty_input) }} Kg</span>
            </div>
            <div class="flex justify-between border-b border-slate-50 pb-2">
              <span class="text-slate-500">Yield (Hasil Akhir)</span>
              <span class="font-semibold text-emerald-600">{{ formatKg(batch.qty_hasil) }} Kg</span>
            </div>
            <div class="flex justify-between border-b border-slate-50 pb-2">
              <span class="text-slate-500">Susut / Tekor</span>
              <span class="font-semibold text-red-500">{{ formatKg(batch.tekor_kg) }} Kg</span>
            </div>
            <div class="flex justify-between pb-1">
              <span class="text-slate-500">Harga Pokok (HPP)</span>
              <span class="font-semibold text-slate-800">
                {{ formatRupiah(hitungHpp(batch)) }} / Kg
              </span>
            </div>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-2xl border border-slate-100 shadow-[0_4px_20px_rgb(0,0,0,0.03)] overflow-hidden">
        <div class="px-5 py-4 border-b border-slate-100 bg-slate-50 flex items-center gap-2">
          <i class="pi pi-box text-blue-600"></i>
          <h3 class="font-bold text-slate-800">Komposisi Bahan Baku (RAW)</h3>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="bg-white border-b border-slate-100">
                <th class="px-5 py-3 font-semibold text-slate-500 text-xs uppercase text-left">Kode/Bahan</th>
                <th class="px-5 py-3 font-semibold text-slate-500 text-xs uppercase text-right">Kuantitas</th>
                <th class="px-5 py-3 font-semibold text-slate-500 text-xs uppercase text-right">Harga Satuan</th>
                <th class="px-5 py-3 font-semibold text-slate-500 text-xs uppercase text-right">Total Nilai</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-50">
              <tr v-if="!komposisi?.raw?.length && !batch.input_raw?.length">
                <td colspan="4" class="px-5 py-8 text-center text-slate-400">Tidak ada data bahan baku.</td>
              </tr>
              <tr v-for="item in (komposisi?.raw || batch.input_raw)" :key="item.id" class="hover:bg-slate-50/50 transition-colors">
                <td class="px-5 py-3 font-medium text-slate-700">{{ item.nama || item.raw_nama || item.produk_nama || item.raw_kode }}</td>
                <td class="px-5 py-3 text-right font-medium">{{ formatKg(item.qty_kg) }} Kg</td>
                <td class="px-5 py-3 text-right text-slate-500">{{ formatRupiah(item.harga_per_kg || 0) }}</td>
                <td class="px-5 py-3 text-right font-medium">{{ formatRupiah(item.nilai || ((item.qty_kg || 0) * (item.harga_per_kg || 0))) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div v-if="batch.jenis === 'BLENDING' || (batch.input_wip && batch.input_wip.length > 0)" class="bg-white rounded-2xl border border-slate-100 shadow-[0_4px_20px_rgb(0,0,0,0.03)] overflow-hidden">
        <div class="px-5 py-4 border-b border-slate-100 bg-slate-50 flex items-center gap-2">
          <i class="pi pi-sync text-purple-600"></i>
          <h3 class="font-bold text-slate-800">Sumber WIP (Fluida Existing)</h3>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="bg-white border-b border-slate-100">
                <th class="px-5 py-3 font-semibold text-slate-500 text-xs uppercase text-left">Nomor Batch</th>
                <th class="px-5 py-3 font-semibold text-slate-500 text-xs uppercase text-left">Nama Hasil</th>
                <th class="px-5 py-3 font-semibold text-slate-500 text-xs uppercase text-right">Kuantitas</th>
                <th class="px-5 py-3 font-semibold text-slate-500 text-xs uppercase text-right">Harga Satuan</th>
                <th class="px-5 py-3 font-semibold text-slate-500 text-xs uppercase text-right">Total Nilai</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-50">
              <tr v-if="!batch.input_wip?.length">
                <td colspan="5" class="px-5 py-8 text-center text-slate-400">Tidak ada sumber WIP.</td>
              </tr>
              <tr v-for="item in batch.input_wip" :key="item.id" class="hover:bg-slate-50/50 transition-colors">
                <td class="px-5 py-3 font-mono font-medium text-slate-700">{{ item.sumber_nomor }}</td>
                <td class="px-5 py-3 text-slate-600">{{ item.sumber_nama }}</td>
                <td class="px-5 py-3 text-right font-medium">{{ formatKg(item.qty_kg) }} Kg</td>
                <td class="px-5 py-3 text-right text-slate-500">{{ formatRupiah(item.harga_per_kg || 0) }}</td>
                <td class="px-5 py-3 text-right font-medium">{{ formatRupiah(item.nilai || ((item.qty_kg || 0) * (item.harga_per_kg || 0))) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div v-if="batch.catatan" class="bg-amber-50 rounded-2xl border border-amber-100 p-5">
        <h3 class="font-bold text-amber-800 mb-2 flex items-center gap-2">
          <i class="pi pi-align-left"></i> Catatan Batch
        </h3>
        <p class="text-sm text-amber-700 whitespace-pre-line">{{ batch.catatan }}</p>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apiBatch } from '../api'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const errorMsg = ref('')
const batch = ref(null)
const komposisi = ref(null)

function formatKg(v) {
  return Number(v || 0).toLocaleString('id-ID', { minimumFractionDigits: 3, maximumFractionDigits: 3 })
}

function formatRupiah(v) {
  return `Rp ${Number(v || 0).toLocaleString('id-ID', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

function formatTanggal(v) {
  if (!v) return '-'
  const d = new Date(v)
  if (isNaN(d)) return v
  return d.toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' }) + ' ' + d.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' })
}

function hitungHpp(b) {
  if (!b) return 0
  const nilai = Number(b.nilai_hasil) || 0
  const qty = Number(b.qty_hasil) || 0
  if (qty > 0) return nilai / qty
  return Number(b.harga_hasil_per_kg || b.harga_per_kg || b.harga_rata) || 0
}

async function muatDetail() {
  const id = route.params.id
  if (!id) {
    errorMsg.value = 'ID Batch tidak valid.'
    loading.value = false
    return
  }

  loading.value = true
  errorMsg.value = ''

  try {
    const resDetail = await apiBatch.detail(id)
    batch.value = resDetail

    try {
      const resKomp = await apiBatch.komposisi(id)
      komposisi.value = resKomp
    } catch (e) {
      komposisi.value = null
    }
  } catch (e) {
    errorMsg.value = e?.response?.data?.detail || 'Gagal memuat detail batch. Pastikan data tersedia.'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  muatDetail()
})
</script>
