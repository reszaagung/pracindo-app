<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-xl md:text-2xl font-bold text-slate-800">Monitor Tangki</h1>
        <p class="text-sm text-slate-500 mt-1">Pantau kapasitas, saldo real-time, dan riwayat fluida di setiap tangki.</p>
      </div>
      <button
        @click="muatData"
        class="inline-flex items-center justify-center gap-2 bg-white border border-slate-200 text-slate-700 text-sm font-semibold px-4 py-2.5 rounded-xl shadow-sm hover:bg-slate-50 active:scale-95 transition-all"
      >
        <i class="pi pi-refresh" :class="{'pi-spin': loading}"></i> Refresh Data
      </button>
    </div>

    <div v-if="errorMsg" class="bg-red-50 text-red-600 border border-red-100 rounded-xl px-4 py-3 text-sm">
      {{ errorMsg }}
    </div>

    <div v-if="loading && tangkis.length === 0" class="flex justify-center items-center py-20 text-slate-400">
      <i class="pi pi-spin pi-spinner text-3xl"></i>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
      <div
        v-for="t in tangkis"
        :key="t.id"
        class="bg-white rounded-2xl border border-slate-100 shadow-[0_4px_20px_rgb(0,0,0,0.03)] flex flex-col overflow-hidden transition-all hover:shadow-md"
      >
        <div class="p-5 border-b border-slate-100 flex justify-between items-start" :class="t.aktif ? 'bg-slate-50' : 'bg-slate-100/50 opacity-75'">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-full flex items-center justify-center" :class="t.aktif ? 'bg-blue-100 text-blue-600' : 'bg-slate-200 text-slate-500'">
              <i class="pi pi-database text-lg"></i>
            </div>
            <div>
              <h3 class="font-bold text-slate-800 text-lg">{{ t.kode }}</h3>
              <p class="text-xs text-slate-500 font-medium">{{ t.nama || 'Tanpa Keterangan' }}</p>
            </div>
          </div>
          <span
            class="text-[10px] font-bold px-2 py-1 rounded-full uppercase tracking-wider"
            :class="t.aktif ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-200 text-slate-600'"
          >
            {{ t.aktif ? 'Aktif' : 'Non-Aktif' }}
          </span>
        </div>

        <div class="p-5 flex-grow flex flex-col justify-center" :class="{'opacity-75': !t.aktif}">
          <template v-if="t.loadingSaldo">
            <div class="flex justify-center items-center py-6 text-slate-400">
              <i class="pi pi-spin pi-spinner text-xl"></i>
            </div>
          </template>

          <template v-else-if="t.saldo">
            <div class="mb-4">
              <p class="text-xs text-slate-500 font-semibold mb-1 uppercase tracking-wide">Total Volume Tersedia</p>
              <p class="text-2xl font-bold" :class="Number(t.saldo.qty) > 0 ? 'text-emerald-600' : 'text-slate-400'">
                {{ formatKg(t.saldo.qty) }} <span class="text-sm font-medium">Kg</span>
              </p>
            </div>
            <div class="grid grid-cols-2 gap-4 pt-4 border-t border-slate-50">
              <div>
                <p class="text-[11px] text-slate-500 font-semibold uppercase">Total Nilai</p>
                <p class="text-sm font-bold text-slate-800 mt-0.5">{{ formatRupiah(t.saldo.nilai) }}</p>
              </div>
              <div>
                <p class="text-[11px] text-slate-500 font-semibold uppercase">Harga Rata-rata</p>
                <p class="text-sm font-bold text-slate-800 mt-0.5 flex items-center gap-1">
                  {{ formatRupiah(t.saldo.harga_rata) }}
                  <i v-if="t.saldo.harga_beragam" class="pi pi-exclamation-triangle text-amber-500 text-[10px]" title="Harga bahan penyusun bervariasi"></i>
                </p>
              </div>
            </div>
          </template>

          <template v-else>
            <p class="text-sm text-slate-400 text-center py-4">Gagal memuat saldo.</p>
          </template>
        </div>

        <div v-if="t.saldo?.batches?.length" class="bg-slate-50 border-t border-slate-100 p-4 max-h-56 overflow-y-auto custom-scrollbar">
          <p class="text-xs font-bold text-slate-600 mb-2 uppercase tracking-wide flex justify-between">
            <span>Komposisi WIP</span>
            <span class="bg-slate-200 text-slate-600 px-1.5 py-0.5 rounded text-[10px]">{{ t.saldo.batches.length }} Batch</span>
          </p>
          <div class="space-y-2">
            <div v-for="b in t.saldo.batches" :key="b.id" class="bg-white p-3 rounded-lg border border-slate-200 text-xs shadow-sm hover:border-blue-200 transition-colors cursor-default">
              <div class="flex justify-between font-semibold text-slate-800 mb-1.5">
                <span class="font-mono text-blue-700">{{ b.nomor }}</span>
                <span class="text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded">{{ formatKg(b.sisa_qty) }} Kg</span>
              </div>
              <div class="flex justify-between text-slate-500 items-end">
                <span class="truncate pr-2 font-medium">{{ b.nama_hasil }}</span>
                <span class="whitespace-nowrap">{{ formatRupiah(b.harga_per_kg) }}<span class="text-[10px]">/Kg</span></span>
              </div>
            </div>
          </div>
        </div>

        <div v-else-if="t.saldo && Number(t.saldo.qty) === 0" class="bg-slate-50 border-t border-slate-100 p-4 text-center">
          <p class="text-xs text-slate-500 font-medium flex items-center justify-center gap-1">
            <i class="pi pi-info-circle"></i> Tangki Kosong
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { apiTangki } from '../api'

const loading = ref(true)
const errorMsg = ref('')
const tangkis = ref([])

function formatKg(v) {
  return Number(v || 0).toLocaleString('id-ID', { minimumFractionDigits: 3, maximumFractionDigits: 3 })
}

function formatRupiah(v) {
  return `Rp ${Number(v || 0).toLocaleString('id-ID', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

async function muatData() {
  loading.value = true
  errorMsg.value = ''
  try {
    const res = await apiTangki.daftar()
    const dataTangki = Array.isArray(res) ? res : (res?.results || [])

    tangkis.value = dataTangki.map(t => ({
      ...t,
      loadingSaldo: true,
      saldo: null
    }))

    await Promise.all(
      tangkis.value.map(async (t) => {
        try {
          if (t.aktif) {
            t.saldo = await apiTangki.saldo(t.id)
          }
        } catch (e) {
          console.error(`Gagal memuat saldo tangki ${t.kode}`, e)
        } finally {
          t.loadingSaldo = false
        }
      })
    )
  } catch (e) {
    errorMsg.value = 'Gagal memuat data tangki. Periksa koneksi Anda.'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  muatData()
})
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style>
