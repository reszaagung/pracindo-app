<template>
    <div class="flex flex-col w-full animate-fade-in relative max-w-md mx-auto min-h-screen bg-slate-50 pb-20">
        <div class="bg-slate-900 pt-8 pb-6 px-6 shadow-md text-white sticky top-0 z-30">
            <div class="flex items-center gap-4">
                <button @click="$router.push('/kurir')" class="w-10 h-10 bg-slate-800 rounded-xl flex items-center justify-center hover:bg-slate-700 transition-colors">
                    <i class="pi pi-arrow-left text-sm"></i>
                </button>
                <div>
                    <h1 class="text-xl font-black tracking-tight">Tugas Saya</h1>
                    <p class="text-xs text-slate-400 mt-0.5">Daftar rute pengiriman hari ini</p>
                </div>
            </div>
        </div>

        <div class="p-5 flex-1">
            <div v-if="sedangMemuat" class="py-12 flex justify-center">
                <i class="pi pi-spin pi-spinner text-3xl text-blue-500"></i>
            </div>

            <div v-else-if="daftarTugasFlattened.length > 0" class="flex flex-col gap-4">
                <div v-for="tugas in daftarTugasFlattened" :key="tugas.perhentian_id"
                    @click="$router.push(`/kurir/tugas/${tugas.perhentian_id}?pengiriman=${tugas.pengiriman_id}`)"
                    class="bg-white border border-slate-200 rounded-[20px] p-5 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden cursor-pointer active:scale-[0.98]">

                    <div class="absolute left-0 top-0 bottom-0 w-1.5" :class="getGarisStatus(tugas.status_tampil)"></div>

                    <div class="flex justify-between items-start mb-3">
                        <div>
                            <span class="px-2 py-0.5 rounded text-[9px] font-black tracking-widest uppercase border bg-blue-50 text-blue-600 border-blue-200">
                                <i class="pi text-[8px] mr-1 pi-box"></i> DO
                            </span>
                            <h2 class="text-base font-black text-slate-800 mt-2">{{ tugas.no_do }}</h2>
                        </div>
                        <span class="px-2.5 py-1 rounded-md text-[10px] font-black tracking-widest uppercase border" :class="getBadgeStatus(tugas.status_tampil)">
                            {{ tugas.status_tampil }}
                        </span>
                    </div>

                    <div class="bg-slate-50 p-3 rounded-xl border border-slate-100">
                        <span class="text-[9px] font-bold text-slate-400 uppercase tracking-wider block mb-0.5">Tujuan</span>
                        <p class="text-sm font-bold text-slate-700 leading-tight line-clamp-1">{{ tugas.tujuan_nama }}</p>
                        <p class="text-xs text-slate-500 mt-1 line-clamp-1"><i class="pi pi-map-marker text-[10px]"></i> {{ tugas.tujuan_alamat }}</p>
                    </div>
                </div>
            </div>

            <div v-else class="py-12 flex flex-col items-center text-center">
                <div class="w-16 h-16 bg-slate-200/50 rounded-full flex items-center justify-center mb-4">
                    <i class="pi pi-check text-emerald-500 text-2xl"></i>
                </div>
                <h3 class="text-base font-bold text-slate-800">Semua Tugas Selesai</h3>
                <p class="text-xs text-slate-500 mt-1">Anda tidak memiliki jadwal aktif saat ini.</p>
            </div>
        </div>
    </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useCourier } from '../composables/useCourier'

const { daftarPengiriman, sedangMemuat, muatTugas } = useCourier()

const daftarTugasFlattened = computed(() => {
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
.animate-fade-in { animation: fadeIn 0.3s ease-out forwards; }
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
</style>
