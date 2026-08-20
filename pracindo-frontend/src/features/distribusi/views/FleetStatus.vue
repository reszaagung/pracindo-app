<template>
  <div class="space-y-6">
    <div class="flex flex-col md:flex-row md:justify-between md:items-end gap-4 mb-8">
      <div>
        <div class="text-xs font-semibold text-slate-400 mb-1 tracking-wider uppercase">Distribution / Status Armada</div>
        <h1 class="text-2xl md:text-3xl font-bold text-slate-800">Pantau Armada</h1>
        <p class="text-slate-500 text-sm mt-1">Ketersediaan truk dan kendaraan saat ini.</p>
      </div>
      <button class="bg-slate-900 hover:bg-slate-800 text-white px-6 py-2.5 rounded-xl font-medium transition-colors flex items-center gap-2 shadow-md">
        <i class="pi pi-plus text-sm"></i>
        <span>Registrasi Armada</span>
      </button>
    </div>

    <div v-if="memuat" class="flex justify-center items-center py-12">
      <i class="pi pi-spin pi-spinner text-3xl text-emerald-500"></i>
    </div>

    <div v-else-if="galat" class="bg-rose-50 border border-rose-200 text-rose-700 p-4 rounded-xl flex items-start gap-3">
      <i class="pi pi-exclamation-triangle mt-0.5"></i>
      <p class="text-sm">{{ galat }}</p>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">

      <div v-if="armadaList.length === 0" class="col-span-full bg-slate-50 border border-slate-200 rounded-2xl p-12 text-center">
        <div class="w-16 h-16 bg-slate-200 rounded-full flex items-center justify-center mx-auto mb-4">
          <i class="pi pi-truck text-2xl text-slate-400"></i>
        </div>
        <h3 class="text-slate-700 font-bold mb-1">Tidak Ada Armada</h3>
        <p class="text-slate-500 text-sm">Belum ada data kendaraan yang terdaftar di sistem.</p>
      </div>

      <div v-for="truk in armadaList" :key="truk.id"
           class="bg-white border rounded-2xl p-6 transition-all duration-300 hover:shadow-lg"
           :class="truk.aktif ? 'border-slate-200' : 'border-rose-100 bg-rose-50/30'">

        <div class="flex justify-between items-start mb-6">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-full flex items-center justify-center"
                 :class="truk.aktif ? 'bg-slate-100 text-slate-600' : 'bg-rose-100 text-rose-500'">
              <i class="pi pi-truck"></i>
            </div>
            <div>
              <h3 class="text-slate-800 font-bold text-lg leading-tight">
                {{ truk.plat_nomor || truk.kode }}
              </h3>
              <p class="text-slate-500 text-xs">{{ truk.nama }}</p>
            </div>
          </div>
          <span class="px-3 py-1 rounded-full text-[10px] font-bold tracking-wider"
                :class="truk.aktif
                  ? 'bg-emerald-100 text-emerald-700 border border-emerald-200'
                  : 'bg-rose-100 text-rose-700 border border-rose-200'">
            {{ truk.aktif ? 'TERSEDIA' : 'PERBAIKAN / NONAKTIF' }}
          </span>
        </div>

        <div class="bg-slate-50 rounded-xl p-4 mb-6 border border-slate-100">
          <p class="text-[10px] font-bold text-slate-400 mb-1 uppercase tracking-wider">Informasi Kendaraan</p>
          <div class="flex items-center gap-2">
            <i class="pi pi-id-card text-slate-400"></i>
            <span class="text-slate-700 text-sm font-medium">Kode: {{ truk.kode }}</span>
          </div>
        </div>

        <div class="flex items-end justify-between pt-4 border-t border-slate-100">
          <div>
            <p class="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-0.5">Kapasitas Maks</p>
            <p class="text-slate-700 font-bold">
              {{ formatKapasitas(truk.kapasitas_kg) }}
            </p>
          </div>
          <button class="text-blue-600 hover:text-blue-700 text-sm font-semibold flex items-center gap-1 group">
            Detail
            <i class="pi pi-arrow-right text-xs transition-transform group-hover:translate-x-1"></i>
          </button>
        </div>

      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { apiDistribusi } from '../api.js'

const armadaList = ref([])
const memuat = ref(true)
const galat = ref(null)

const formatKapasitas = (kg) => {
  if (!kg) return 'Tidak disetel'
  const angka = parseFloat(kg)
  if (angka >= 1000) {
    return `${(angka / 1000).toLocaleString('id-ID')} Ton`
  }
  return `${angka.toLocaleString('id-ID')} Kg`
}

const muatDataArmada = async () => {
  memuat.value = true
  galat.value = null
  try {
    const data = await apiDistribusi.getArmada()
    armadaList.value = data.results || data || []
  } catch (error) {
    galat.value = "Gagal memuat daftar kendaraan dari server. Pastikan Anda memiliki akses."
  } finally {
    memuat.value = false
  }
}

onMounted(() => {
  muatDataArmada()
})
</script>
