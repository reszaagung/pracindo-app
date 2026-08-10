<!-- src/features/distribusi/views/CourierTask.vue -->
<template>
    <div class="flex flex-col w-full animate-fade-in relative max-w-3xl mx-auto">
        <!-- Header Profil Supir -->
        <div
            class="mb-6 bg-slate-900 rounded-[24px] p-5 shadow-lg text-white flex justify-between items-center relative overflow-hidden">
            <div class="relative z-10">
                <p class="text-slate-400 text-xs font-bold uppercase tracking-wider mb-1">Mode Kurir Lapangan</p>
                <h1 class="text-xl md:text-2xl font-black tracking-tight">Tugas Hari Ini</h1>
                <p class="text-sm text-slate-300 mt-1"><i class="pi pi-truck mr-1 text-xs"></i> L 8821 XA</p>
            </div>
            <div
                class="w-14 h-14 bg-slate-800 rounded-full flex items-center justify-center border-2 border-slate-700 relative z-10 shadow-inner">
                <i class="pi pi-user text-2xl text-slate-300"></i>
            </div>
            <!-- Ornamen Dekorasi -->
            <div class="absolute -right-10 -bottom-10 w-40 h-40 bg-white/5 rounded-full blur-2xl"></div>
        </div>

        <!-- Daftar Pengiriman (Mobile-Optimized Cards) -->
        <div class="flex flex-col gap-5">
            <div v-for="tugas in daftarTugas" :key="tugas.id"
                class="bg-white border border-slate-200 rounded-[20px] p-5 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden">

                <!-- Garis Indikator Status di Samping -->
                <div class="absolute left-0 top-0 bottom-0 w-1.5" :class="getGarisStatus(tugas.status)"></div>

                <div class="flex justify-between items-start mb-4">
                    <div>
                        <span class="px-2.5 py-1 rounded-md text-[10px] font-black tracking-widest uppercase border"
                            :class="getBadgeStatus(tugas.status)">
                            {{ tugas.status }}
                        </span>
                        <h2 class="text-lg font-black text-slate-800 mt-2">{{ tugas.no_do }}</h2>
                    </div>
                    <button
                        class="w-10 h-10 rounded-full bg-slate-50 text-slate-500 hover:bg-slate-100 flex items-center justify-center border border-slate-200 transition-colors">
                        <i class="pi pi-map-marker"></i>
                    </button>
                </div>

                <div class="space-y-3 mb-5 bg-slate-50 p-4 rounded-xl border border-slate-100">
                    <div>
                        <span
                            class="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-0.5">Penerima
                            / Toko</span>
                        <p class="text-sm font-bold text-slate-800">{{ tugas.tujuan_nama }}</p>
                    </div>
                    <div>
                        <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-0.5">Alamat
                            Pengiriman</span>
                        <p class="text-xs text-slate-600 leading-relaxed">{{ tugas.tujuan_alamat }}</p>
                    </div>
                </div>

                <!-- Tombol Aksi (Dinamis Berdasarkan Status) -->
                <div class="flex gap-3">
                    <button v-if="tugas.status === 'SIAP JALAN'" @click="updateStatus(tugas, 'OTW')"
                        class="flex-1 py-3.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-bold rounded-xl shadow-md transition-colors flex justify-center items-center gap-2">
                        <i class="pi pi-play text-xs"></i> Mulai Perjalanan
                    </button>

                    <button v-if="tugas.status === 'OTW'" @click="updateStatus(tugas, 'SAMPAI')"
                        class="flex-1 py-3.5 bg-amber-500 hover:bg-amber-600 text-white text-sm font-bold rounded-xl shadow-md transition-colors flex justify-center items-center gap-2">
                        <i class="pi pi-stop-circle text-xs"></i> Tiba di Lokasi
                    </button>

                    <button v-if="tugas.status === 'SAMPAI'" @click="bukaModalPOD(tugas)"
                        class="flex-1 py-3.5 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-bold rounded-xl shadow-[0_4px_15px_rgba(16,185,129,0.3)] transition-colors flex justify-center items-center gap-2">
                        <i class="pi pi-camera text-xs"></i> Upload Bukti Terima
                    </button>

                    <div v-if="tugas.status === 'SELESAI'"
                        class="flex-1 py-3 bg-slate-100 text-slate-500 text-sm font-bold rounded-xl flex justify-center items-center gap-2 border border-slate-200 cursor-not-allowed">
                        <i class="pi pi-check-circle text-emerald-500"></i> Tugas Selesai
                    </div>
                </div>
            </div>
        </div>

        <!-- State Kosong -->
        <div v-if="daftarTugas.length === 0"
            class="mt-8 flex flex-col items-center justify-center p-8 bg-white border border-slate-200 rounded-[24px] text-center">
            <div
                class="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center mb-4 border border-slate-100">
                <i class="pi pi-check text-emerald-500 text-2xl"></i>
            </div>
            <h3 class="text-base font-bold text-slate-800">Semua Tugas Selesai!</h3>
            <p class="text-xs text-slate-500 mt-1">Anda tidak memiliki jadwal pengiriman aktif saat ini.</p>
        </div>

        <!-- Modal POD (Proof of Delivery) -->
        <div v-if="tugasTerpilih"
            class="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-slate-900/60 backdrop-blur-sm sm:p-4">
            <div
                class="bg-white w-full max-w-md sm:rounded-[24px] rounded-t-[24px] shadow-2xl flex flex-col animate-fade-in-up">
                <div
                    class="px-5 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50/50 rounded-t-[24px]">
                    <h3 class="text-sm font-bold text-slate-800">Bukti Pengiriman (POD)</h3>
                    <button @click="tugasTerpilih = null"
                        class="w-8 h-8 rounded-full bg-slate-100 text-slate-500 hover:text-red-500 transition-colors flex items-center justify-center">
                        <i class="pi pi-times text-sm"></i>
                    </button>
                </div>

                <div class="p-5 space-y-4">
                    <div class="flex flex-col gap-1.5">
                        <label class="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Nama
                            Penerima</label>
                        <input type="text" v-model="formPOD.penerima" placeholder="Nama orang yang menerima barang..."
                            class="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 text-slate-800 font-medium" />
                    </div>

                    <div class="flex flex-col gap-1.5">
                        <label class="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Foto Bukti Surat
                            Jalan / Barang</label>
                        <label
                            class="w-full h-32 border-2 border-dashed border-slate-300 rounded-xl bg-slate-50 flex flex-col items-center justify-center cursor-pointer hover:bg-slate-100 hover:border-emerald-500 transition-colors group">
                            <i class="pi pi-camera text-2xl text-slate-400 group-hover:text-emerald-500 mb-2"></i>
                            <span class="text-xs font-bold text-slate-500 group-hover:text-emerald-600">Ambil Foto /
                                Pilih File</span>
                            <input type="file" accept="image/*" class="hidden" @change="handleFotoUpload" />
                        </label>
                        <p v-if="formPOD.foto" class="text-xs text-emerald-600 font-bold mt-1 text-center"><i
                                class="pi pi-check-circle"></i> Foto siap diunggah</p>
                    </div>
                </div>

                <div class="p-5 border-t border-slate-100 bg-white">
                    <button @click="kirimPOD" :disabled="!formPOD.penerima"
                        class="w-full py-3.5 bg-slate-900 hover:bg-slate-800 text-white text-sm font-bold rounded-xl shadow-md transition-colors flex justify-center items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed">
                        <i class="pi pi-cloud-upload"></i> Selesaikan Tugas
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, reactive } from 'vue'

// Dummy Data
const daftarTugas = ref([
    {
        id: 1,
        no_do: 'DO-202608-002',
        tujuan_nama: 'Depo Bangunan Pusat',
        tujuan_alamat: 'Kawasan Pergudangan Margomulyo, Surabaya',
        status: 'SIAP JALAN'
    },
    {
        id: 2,
        no_do: 'DO-202608-003',
        tujuan_nama: 'Toko Besi Makmur',
        tujuan_alamat: 'Jl. Ahmad Yani No 45, Sidoarjo',
        status: 'OTW'
    }
])

const tugasTerpilih = ref(null)
const formPOD = reactive({ penerima: '', foto: null })

const getBadgeStatus = (status) => {
    switch (status) {
        case 'SIAP JALAN': return 'bg-slate-50 text-slate-600 border-slate-200'
        case 'OTW': return 'bg-blue-50 text-blue-600 border-blue-200'
        case 'SAMPAI': return 'bg-amber-50 text-amber-600 border-amber-200'
        case 'SELESAI': return 'bg-emerald-50 text-emerald-600 border-emerald-200'
        default: return 'bg-slate-50 text-slate-500 border-slate-200'
    }
}

const getGarisStatus = (status) => {
    switch (status) {
        case 'SIAP JALAN': return 'bg-slate-300'
        case 'OTW': return 'bg-blue-500'
        case 'SAMPAI': return 'bg-amber-500'
        case 'SELESAI': return 'bg-emerald-500'
        default: return 'bg-slate-300'
    }
}

const updateStatus = (tugas, statusBaru) => {
    tugas.status = statusBaru
}

const bukaModalPOD = (tugas) => {
    tugasTerpilih.value = tugas
    formPOD.penerima = ''
    formPOD.foto = null
}

const handleFotoUpload = (e) => {
    if (e.target.files.length > 0) {
        formPOD.foto = e.target.files[0]
    }
}

const kirimPOD = () => {
    if (tugasTerpilih.value) {
        tugasTerpilih.value.status = 'SELESAI'
        alert(`Bukti pengiriman (POD) untuk ${tugasTerpilih.value.no_do} berhasil diunggah!`)
        tugasTerpilih.value = null
    }
}
</script>

<style scoped>
.animate-fade-in {
    animation: fadeIn 0.4s ease-out forwards;
}

.animate-fade-in-up {
    animation: fadeInUp 0.3s ease-out forwards;
}

@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(100%);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}
</style>