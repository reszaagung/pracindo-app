<template>
  <div class="space-y-6">
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 class="text-xl md:text-2xl font-bold text-slate-800">Riwayat Batch Produksi</h1>
        <p class="text-sm text-slate-500 mt-1">Daftar seluruh batch mixing &amp; blending yang tercatat.</p>
      </div>
      <router-link
        :to="{ name: 'produksi-batch-buat' }"
        class="inline-flex items-center gap-2 bg-white border border-slate-200 text-slate-700 text-sm font-bold px-4 py-2.5 rounded-xl shadow-sm hover:bg-slate-50 active:scale-95 transition-all self-start sm:self-auto"
      >
        <i class="pi pi-plus text-sm text-slate-500"></i>
        Input Baru
      </router-link>
    </div>

    <p v-if="errorMsg" class="text-sm bg-red-50 text-red-600 border border-red-100 rounded-xl px-4 py-2.5">
      {{ errorMsg }}
    </p>

    <div class="bg-white rounded-2xl border border-slate-100 shadow-[0_4px_20px_rgb(0,0,0,0.03)] p-4">
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
       <div class="relative lg:col-span-2">
          <i class="pi pi-search absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 text-sm pointer-events-none"></i>
          <input
            v-model="filter.search"
            type="text"
            placeholder="Cari nomor batch / nama hasil..."
            class="w-full pl-10 pr-3 py-2.5 rounded-xl border border-slate-200 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-slate-900/10 focus:border-slate-300"
            @input="cariDenganDebounce"
          />
        </div>

        <select
          v-model="filter.jenis"
          class="w-full py-2.5 px-3 rounded-xl border border-slate-200 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-slate-900/10"
          @change="muatUlang"
        >
          <option v-for="opt in JENIS_BATCH_OPTIONS" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
        </select>
      </div>
    </div>

    <div class="bg-white rounded-2xl border border-slate-100 shadow-[0_4px_20px_rgb(0,0,0,0.03)] overflow-hidden">
      <div v-if="!isMobile" class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="bg-slate-50 border-b border-slate-100">
              <th
                v-for="col in BATCH_TABLE_COLUMNS"
                :key="col.key"
                class="px-4 py-3 font-semibold text-slate-500 text-xs uppercase tracking-wide whitespace-nowrap"
                :class="alignClass(col.align)"
              >
                {{ col.label }}
              </th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-50">
            <tr v-if="loading">
              <td :colspan="BATCH_TABLE_COLUMNS.length" class="px-4 py-10 text-center text-slate-400">
                <i class="pi pi-spin pi-spinner mr-2"></i>Memuat data...
              </td>
            </tr>
            <tr v-else-if="baris.length === 0">
              <td :colspan="BATCH_TABLE_COLUMNS.length" class="px-4 py-10 text-center text-slate-400">
                Belum ada batch produksi yang cocok dengan filter.
              </td>
            </tr>
            <tr v-for="row in baris" :key="row.id" class="hover:bg-slate-50/70 transition-colors">
              <template v-for="col in BATCH_TABLE_COLUMNS" :key="col.key">
                <td v-if="col.key === 'aksi'" class="px-4 py-3 whitespace-nowrap" :class="alignClass(col.align)">
                  <div class="flex items-center gap-1.5 justify-center">
                    <button
                      title="Lihat Detail"
                      class="w-8 h-8 rounded-lg flex items-center justify-center text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition-colors"
                      @click="router.push({ name: 'produksi-batch-detail', params: { id: row.id } })"
                    >
                      <i class="pi pi-eye text-sm"></i>
                    </button>
                  </div>
                </td>
                
                <td v-else-if="col.key === 'status'" class="px-4 py-3 whitespace-nowrap" :class="alignClass(col.align)">
                  <span
                    class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold border"
                    :class="Number(row.qty_hasil) > 0 ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-amber-50 text-amber-700 border-amber-200'"
                  >
                    {{ Number(row.qty_hasil) > 0 ? 'SELESAI' : 'PROSES' }}
                  </span>
                </td>

                <td v-else-if="col.key === 'jenis'" class="px-4 py-3 whitespace-nowrap text-slate-600" :class="alignClass(col.align)">
                  {{ JENIS_BATCH_LABELS[row.jenis] || row.jenis }}
                </td>
                
                <td v-else-if="col.key === 'waktu'" class="px-4 py-3 whitespace-nowrap text-slate-500" :class="alignClass(col.align)">
                  {{ formatTanggal(row.waktu) }}
                </td>
                
                <td v-else-if="col.key === 'qty_hasil'" class="px-4 py-3 whitespace-nowrap text-slate-700 font-medium" :class="alignClass(col.align)">
                  {{ formatAngka(row.qty_hasil) }} Kg
                </td>
                
                <td v-else-if="col.key === 'harga_per_kg' || col.key === 'harga_rata'" class="px-4 py-3 whitespace-nowrap text-slate-700" :class="alignClass(col.align)">
                  {{ formatRupiah(ambilHarga(row)) }}
                </td>
                
                <td v-else-if="col.key === 'batch'" class="px-4 py-3 whitespace-nowrap font-mono text-slate-800 font-medium" :class="alignClass(col.align)">
                  {{ row.batch }}
                </td>
                
                <td v-else class="px-4 py-3 whitespace-nowrap text-slate-600" :class="alignClass(col.align)">
                  {{ row[col.key] ?? '-' }}
                </td>
              </template>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Tampilan Mobile -->
      <div v-else class="flex flex-col gap-4 p-4 bg-slate-50">
        <div v-if="loading" class="text-center text-slate-400 py-10">
          <i class="pi pi-spin pi-spinner mr-2"></i>Memuat data...
        </div>
        <div v-else-if="baris.length === 0" class="text-center text-slate-400 py-10">
          Belum ada batch produksi yang cocok dengan filter.
        </div>
        <div v-for="row in baris" :key="row.id" class="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex flex-col gap-3">
          <div class="flex justify-between items-start border-b border-slate-100 pb-3">
            <div>
              <h3 class="font-mono font-bold text-slate-800">{{ row.batch }}</h3>
              <p class="text-xs text-slate-500 mt-1">{{ formatTanggal(row.waktu) }}</p>
            </div>
            <span 
              class="inline-flex items-center px-2.5 py-1 rounded-full text-[10px] font-semibold border"
              :class="Number(row.qty_hasil) > 0 ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-amber-50 text-amber-700 border-amber-200'"
            >
              {{ Number(row.qty_hasil) > 0 ? 'SELESAI' : 'PROSES' }}
            </span>
          </div>

          <div class="grid grid-cols-2 gap-2 text-xs">
            <div class="flex flex-col gap-1">
              <span class="text-slate-400 font-semibold uppercase">Jenis</span>
              <span class="text-slate-700">{{ JENIS_BATCH_LABELS[row.jenis] || row.jenis }}</span>
            </div>
            <div class="flex flex-col gap-1">
              <span class="text-slate-400 font-semibold uppercase">Nama Hasil</span>
              <span class="text-slate-700 font-medium">{{ row.nama_hasil }}</span>
            </div>
            <div class="flex flex-col gap-1">
              <span class="text-slate-400 font-semibold uppercase">Yield</span>
              <span class="text-slate-800 font-bold">{{ formatAngka(row.qty_hasil) }} Kg</span>
            </div>
            <div class="flex flex-col gap-1">
              <span class="text-slate-400 font-semibold uppercase">Nominal/Kg</span>
              <span class="text-slate-700">{{ formatRupiah(ambilHarga(row)) }}</span>
            </div>
          </div>

          <div class="mt-2 pt-3 border-t border-slate-100 flex gap-2 justify-end">
            <button class="px-4 py-2 text-xs font-bold bg-white border border-slate-200 text-slate-700 rounded-xl shadow-sm hover:bg-slate-50 flex-1" @click="router.push({ name: 'produksi-batch-detail', params: { id: row.id } })">
              Detail
            </button>
          </div>
        </div>
      </div>

      <!-- Paginasi -->
      <div
        v-if="!loading && baris.length > 0"
        class="flex items-center justify-between px-4 py-3 border-t border-slate-100 text-sm text-slate-500 bg-white"
      >
        <span>Halaman {{ halaman }}{{ totalHalaman ? ` dari ${totalHalaman}` : '' }}</span>
        <div class="flex gap-2">
          <button
            class="px-3 py-1.5 rounded-lg border border-slate-200 disabled:opacity-40 hover:bg-slate-50 transition-colors"
            :disabled="halaman <= 1 || loading"
            @click="gantiHalaman(halaman - 1)"
          >
            <i class="pi pi-chevron-left text-xs"></i>
          </button>
          <button
            class="px-3 py-1.5 rounded-lg border border-slate-200 disabled:opacity-40 hover:bg-slate-50 transition-colors"
            :disabled="!adaHalamanBerikut || loading"
            @click="gantiHalaman(halaman + 1)"
          >
            <i class="pi pi-chevron-right text-xs"></i>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { apiBatch } from '../api'
import { useLayout } from '@/composables/useLayout'
import {
  BATCH_TABLE_COLUMNS,
  JENIS_BATCH_OPTIONS,
  JENIS_BATCH_LABELS
} from '../uiConfigProduksi'

const router = useRouter()
const { isMobile } = useLayout()
const baris = ref([])
const loading = ref(false)
const errorMsg = ref('')
const filter = reactive({ jenis: '', search: '' }) // filter status dihapus
const halaman = ref(1)
const totalHalaman = ref(0)
const adaHalamanBerikut = ref(false)
let timerDebounce = null

function alignClass(align) {
  if (align === 'right') return 'text-right'
  if (align === 'center') return 'text-center'
  return 'text-left'
}

function formatTanggal(v) {
  if (!v) return '-'
  const d = new Date(v)
  if (isNaN(d)) return v
  return (
    d.toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' }) +
    ' ' +
    d.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' })
  )
}

function formatAngka(v) {
  return Number(v || 0).toLocaleString('id-ID', { minimumFractionDigits: 3, maximumFractionDigits: 3 })
}

function formatRupiah(v) {
  return `Rp ${Number(v || 0).toLocaleString('id-ID', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

function ambilHarga(row) {
  const nilai = Number(row.nilai_hasil) || 0
  const qty = Number(row.qty_hasil) || 0
  if (qty > 0) {
    return nilai / qty
  }
  const h1 = Number(row.harga_hasil_per_kg) || 0
  const h2 = Number(row.harga_rata) || 0
  const h3 = (row.harga_per_kg === 'None') ? 0 : (Number(row.harga_per_kg) || 0)
  return h1 || h2 || h3 || 0
}

async function muatData() {
  loading.value = true
  errorMsg.value = ''
  try {
    const params = { page: halaman.value }
    if (filter.jenis) params.jenis = filter.jenis
    if (filter.search) params.search = filter.search
    const res = await apiBatch.daftar(params)

    if (Array.isArray(res)) {
      baris.value = res
      totalHalaman.value = 0
      adaHalamanBerikut.value = false
    } else {
      baris.value = res?.results ?? []
      adaHalamanBerikut.value = Boolean(res?.next)
      const pageSize = baris.value.length || 1
      totalHalaman.value = res?.count ? Math.ceil(res.count / pageSize) : 0
    }
  } catch {
    errorMsg.value = 'Gagal memuat daftar batch produksi'
    baris.value = []
  } finally {
    loading.value = false
  }
}

function muatUlang() {
  halaman.value = 1
  muatData()
}

function cariDenganDebounce() {
  clearTimeout(timerDebounce)
  timerDebounce = setTimeout(muatUlang, 400)
}

function gantiHalaman(h) {
  if (h < 1) return
  halaman.value = h
  muatData()
}

onMounted(muatData)
</script>