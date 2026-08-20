<template>
  <div class="flex-1 overflow-y-auto pb-24 bg-slate-50">

    <!-- Header Profil (Dark Mode) -->
    <div class="bg-slate-900 px-6 pt-12 pb-8 rounded-b-[2rem] shadow-md relative z-10">
      <div class="flex justify-between items-center mb-6">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 bg-slate-800 rounded-full flex items-center justify-center border-2 border-emerald-500">
            <i class="pi pi-user text-slate-300 text-xl"></i>
          </div>
          <div>
            <p class="text-emerald-400 text-xs font-bold tracking-wider uppercase">Kurir Internal</p>
            <h2 class="text-white text-xl font-bold">Resza</h2>
            <p class="text-slate-400 text-sm">Staf</p>
          </div>
        </div>
        <button class="w-10 h-10 bg-slate-800 rounded-full flex items-center justify-center text-slate-300 hover:text-white transition-colors shadow-inner">
          <i class="pi pi-bell"></i>
        </button>
      </div>

      <!-- Kartu Absensi -->
      <div class="bg-slate-800/80 border border-slate-700 rounded-2xl p-4 flex items-center justify-between">
        <div>
          <p class="text-slate-400 text-xs mb-1">Status Kehadiran</p>
          <div class="flex items-center gap-2 text-rose-400">
            <i class="pi pi-times-circle"></i>
            <span class="font-bold text-sm">Belum Absen Masuk</span>
          </div>
        </div>
        <button class="bg-emerald-500 hover:bg-emerald-600 text-white text-sm font-bold py-2 px-4 rounded-xl transition-colors">
          Absen Masuk
        </button>
      </div>
    </div>

    <!-- Area Daftar Tugas -->
    <div class="px-6 py-8 relative z-0">
      <h3 class="text-lg font-bold text-slate-800 mb-4">Daftar Tugas</h3>

      <!-- Placeholder Tidak Ada Tugas -->
      <div class="bg-white border border-slate-200 rounded-2xl p-8 flex flex-col items-center justify-center text-center shadow-sm">
        <div class="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center text-slate-400 mb-4">
          <i class="pi pi-check-square text-2xl"></i>
        </div>
        <h4 class="text-slate-800 font-bold mb-2">Tidak Ada Tugas</h4>
        <p class="text-slate-500 text-sm">Anda tidak memiliki jadwal pengiriman aktif saat ini.</p>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import { useCourier } from '../composables/useCourier'

const router = useRouter()
const { kartu } = useAuth()
const { daftarPengiriman, sedangMemuat, muatTugas, berangkatkan, tandaiSampai } = useCourier()

const userNama = computed(() => kartu.value?.nama || 'Kurir Logistik')
const userRole = computed(() => kartu.value?.role_display || 'Staff Distribusi')
const isClockedIn = ref(false)

const tugasTefilter = computed(() => {
    const tugas = []
    daftarPengiriman.value.forEach(kirim => {
        kirim.perhentian?.forEach(stop => {
            let statusTampil = stop.status
            if (kirim.status === 'DISIAPKAN') statusTampil = 'SIAP JALAN'
            else if (stop.status === 'MENUNGGU' && kirim.status === 'BERANGKAT') statusTampil = 'OTW'

            tugas.push({
                pengiriman_id: kirim.id,
                perhentian_id: stop.id,
                no_do: stop.nomor_distribusi || 'DO-SYSTEM',
                tujuan_nama: stop.pelanggan_nama || stop.pelanggan,
                tujuan_alamat: stop.alamat,
                status_pengiriman: kirim.status,
                status_perhentian: stop.status,
                status_tampil: statusTampil
            })
        })
    })
    return tugas
})

const armadaAktif = computed(() => {
    if (daftarPengiriman.value.length > 0) return daftarPengiriman.value[0].kendaraan_kode || 'Truk Reguler'
    return 'Belum Ditugaskan'
})

const toggleAbsen = () => {
    if (isClockedIn.value) {
        if (confirm('Akhiri shift hari ini?')) isClockedIn.value = false
    } else {
        isClockedIn.value = true
    }
}

const aksiBerangkat = async (id) => {
    if (confirm("Mulai perjalanan?")) await berangkatkan(id)
}

const aksiTiba = async (pId, hId) => {
    await tandaiSampai(pId, hId)
}

const bukaTugas = () => {
    router.push('/distribusi/kurir/task')
}

const getBadgeStatus = (status) => {
    switch (status) {
        case 'SIAP JALAN': return 'bg-slate-100 text-slate-500 border-slate-200'
        case 'OTW': return 'bg-amber-50 text-amber-600 border-amber-200'
        case 'SAMPAI': return 'bg-blue-50 text-blue-600 border-blue-200'
        case 'DITERIMA':
        case 'DIRETUR':
        case 'SELESAI': return 'bg-emerald-50 text-emerald-600 border-emerald-200'
        default: return 'bg-slate-50 text-slate-500 border-slate-200'
    }
}

const getGarisStatus = (status) => {
    switch (status) {
        case 'DITERIMA':
        case 'DIRETUR':
        case 'SELESAI': return 'bg-emerald-500'
        default: return 'bg-blue-500'
    }
}

onMounted(() => {
    muatTugas()
})
</script>

<style scoped>
.animate-fade-in { animation: fadeIn 0.4s ease-out forwards; }
.animate-fade-in-up { animation: fadeInUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}
@media (min-width: 640px) {
    .max-w-md {
        max-width: 440px !important;
        margin-top: 2rem;
        margin-bottom: 2rem;
        border-radius: 2.5rem;
        overflow: hidden;
    }
}
</style>
