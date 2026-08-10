<!--
  src/features/logistik/views/TabletCourierApp.vue
  Mockup Aplikasi Tablet Khusus Kurir (Role.KURIR)
-->
<template>
    <div class="flex h-screen bg-slate-100 font-sans text-slate-800 overflow-hidden">

        <!-- PANEL KIRI: Daftar Urutan Tugas (Master) -->
        <aside class="w-1/3 bg-white border-r border-slate-200 flex flex-col h-full z-10 shadow-sm">
            <!-- Header Profil Kurir -->
            <div class="p-6 border-b border-slate-100 bg-slate-900 text-white">
                <div class="flex justify-between items-center mb-4">
                    <div class="flex items-center gap-3">
                        <div
                            class="w-12 h-12 bg-slate-700 rounded-full flex items-center justify-center border-2 border-slate-600">
                            <i class="pi pi-user text-xl"></i>
                        </div>
                        <div>
                            <h2 class="font-bold text-lg leading-tight">Budi Santoso</h2>
                            <p class="text-xs text-slate-400">ID: KURIR-001 &bull; L 8821 XA</p>
                        </div>
                    </div>
                    <button
                        class="w-10 h-10 bg-slate-800 rounded-xl flex items-center justify-center active:scale-95 transition-transform text-rose-400 hover:bg-rose-500 hover:text-white"
                        title="Keluar">
                        <i class="pi pi-power-off"></i>
                    </button>
                </div>
                <div class="bg-slate-800 rounded-lg p-3 flex justify-between items-center border border-slate-700">
                    <span class="text-sm font-semibold text-emerald-400 flex items-center gap-2">
                        <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                        BERANGKAT
                    </span>
                    <span class="text-xs font-bold text-slate-300">DO-202608-002</span>
                </div>
            </div>

            <!-- List Perhentian -->
            <div class="flex-1 overflow-y-auto custom-scrollbar p-4">
                <h3 class="text-xs font-black text-slate-400 uppercase tracking-widest mb-4 px-2">Urutan Pengiriman</h3>

                <div class="flex flex-col gap-3">
                    <button v-for="(stop, index) in daftarPerhentian" :key="stop.id" @click="pilihPerhentian(stop)"
                        class="w-full text-left p-4 rounded-2xl border-2 transition-all duration-200 relative overflow-hidden"
                        :class="[
                            perhentianAktif?.id === stop.id
                                ? 'bg-blue-50 border-blue-500 shadow-md'
                                : 'bg-white border-slate-100 hover:border-slate-300',
                            stop.status === 'DITERIMA' ? 'opacity-60' : ''
                        ]">

                        <div class="flex justify-between items-start mb-1">
                            <span class="text-[10px] font-black px-2 py-1 rounded-md mb-2 inline-block"
                                :class="badgeStatus(stop.status)">
                                {{ index + 1 }}. {{ stop.status }}
                            </span>
                            <span class="text-xs font-bold text-slate-400">{{ stop.estimasi_menit }} mnt</span>
                        </div>
                        <h4 class="font-bold text-base text-slate-800">{{ stop.pelanggan_nama }}</h4>
                        <p class="text-xs text-slate-500 line-clamp-1 mt-1"><i
                                class="pi pi-map-marker text-[10px] mr-1"></i>{{ stop.alamat }}</p>
                    </button>
                </div>
            </div>
        </aside>

        <!-- PANEL KANAN: Detail & Aksi (Detail) -->
        <main class="w-2/3 flex flex-col h-full bg-slate-50 relative">
            <template v-if="perhentianAktif">
                <!-- Area Peta Mockup -->
                <div class="h-2/5 bg-slate-200 w-full relative border-b border-slate-300">
                    <img src="https://www.transparenttextures.com/patterns/cubes.png"
                        class="absolute inset-0 w-full h-full object-cover opacity-20" alt="Map pattern">
                    <div class="absolute inset-0 flex flex-col items-center justify-center">
                        <i class="pi pi-map text-5xl text-slate-400 mb-2 drop-shadow-md"></i>
                        <span
                            class="bg-white/90 backdrop-blur px-4 py-2 rounded-xl text-sm font-bold text-slate-700 shadow-sm border border-slate-200">
                            Map Interaktif (Menunggu API Provider)
                        </span>
                    </div>
                </div>

                <!-- Info Detail -->
                <div class="p-8 flex-1 flex flex-col">
                    <div class="flex justify-between items-start mb-6">
                        <div>
                            <h1 class="text-3xl font-black text-slate-800 mb-2">{{ perhentianAktif.pelanggan_nama }}
                            </h1>
                            <p class="text-slate-600 text-lg flex items-center gap-2">
                                <i class="pi pi-map-marker text-blue-500"></i> {{ perhentianAktif.alamat }}
                            </p>
                        </div>
                        <div class="text-right">
                            <p class="text-sm font-bold text-slate-400 uppercase tracking-wider mb-1">No. Distribusi</p>
                            <p class="text-xl font-bold text-slate-700">{{ perhentianAktif.nomor_distribusi }}</p>
                        </div>
                    </div>

                    <div class="grid grid-cols-2 gap-4 mb-auto">
                        <div class="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm">
                            <p class="text-xs font-bold text-slate-400 uppercase mb-1">Koordinat (Lat, Lng)</p>
                            <p class="font-semibold text-slate-700">{{ perhentianAktif.lat }}, {{ perhentianAktif.lng }}
                            </p>
                        </div>
                        <div class="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm">
                            <p class="text-xs font-bold text-slate-400 uppercase mb-1">Jarak dari Titik Sebelumnya</p>
                            <p class="font-semibold text-slate-700">{{ perhentianAktif.jarak_km }} KM</p>
                        </div>
                    </div>

                    <!-- Tombol Aksi Lapangan (Hanya muncul jika belum tuntas) -->
                    <div v-if="perhentianAktif.status !== 'DITERIMA' && perhentianAktif.status !== 'DIRETUR'"
                        class="bg-white p-6 rounded-[24px] shadow-lg border border-slate-200 mt-6 flex gap-4">

                        <!-- Aksi 1: Sampai Lokasi -->
                        <button v-if="perhentianAktif.status === 'MENUNGGU'"
                            class="flex-1 py-4 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-bold text-lg transition-transform active:scale-95 shadow-md flex items-center justify-center gap-3">
                            <i class="pi pi-check-circle text-xl"></i> Tandai Sampai Lokasi
                        </button>

                        <!-- Aksi 2 & 3: Unggah Bukti & Retur (Muncul setelah ditandai sampai) -->
                        <template v-if="perhentianAktif.status === 'SAMPAI'">
                            <button
                                class="flex-1 py-4 bg-emerald-500 hover:bg-emerald-600 text-white rounded-xl font-bold text-lg transition-transform active:scale-95 shadow-md flex items-center justify-center gap-3">
                                <i class="pi pi-camera text-xl"></i> Ambil Foto Bukti
                            </button>
                            <button
                                class="px-8 py-4 bg-rose-50 hover:bg-rose-100 text-rose-600 border border-rose-200 rounded-xl font-bold text-lg transition-transform active:scale-95 shadow-sm flex items-center justify-center gap-3"
                                title="Catat Retur">
                                <i class="pi pi-times-circle text-xl"></i> Tolak
                            </button>
                        </template>
                    </div>

                    <!-- Peringatan jika sudah tuntas -->
                    <div v-else
                        class="bg-emerald-50 p-6 rounded-[24px] border border-emerald-200 mt-6 flex items-center justify-center gap-3 text-emerald-600">
                        <i class="pi pi-verified text-2xl"></i>
                        <span class="font-bold text-lg">Perhentian ini sudah selesai ({{ perhentianAktif.status
                            }}).</span>
                    </div>

                </div>
            </template>

            <!-- State Kosong -->
            <div v-else class="flex-1 flex flex-col items-center justify-center text-slate-400">
                <i class="pi pi-truck text-6xl mb-4 opacity-50"></i>
                <p class="text-lg font-bold">Pilih perhentian di menu sebelah kiri.</p>
            </div>
        </main>
    </div>
</template>

<script setup>
import { ref } from 'vue'

// Mock Data berdasarkan tests.py (DISTRIBUSI)
const daftarPerhentian = ref([
    {
        id: 1,
        nomor_distribusi: 'DIST/2026/08/001',
        pelanggan_nama: 'Toko Jaya',
        alamat: 'Jl. Merdeka 1',
        lat: '-6.2000',
        lng: '106.8160',
        estimasi_menit: 20,
        jarak_km: '15.2',
        status: 'DITERIMA' // Sudah beres
    },
    {
        id: 2,
        nomor_distribusi: 'DIST/2026/08/002',
        pelanggan_nama: 'Toko Sentosa',
        alamat: 'Jl. Sudirman 9',
        lat: '-6.2250',
        lng: '106.8000',
        estimasi_menit: 15,
        jarak_km: '4.5',
        status: 'SAMPAI' // Sedang ditangani (tunggu foto)
    },
    {
        id: 3,
        nomor_distribusi: 'DIST/2026/08/003',
        pelanggan_nama: 'Toko Makmur',
        alamat: 'Jl. Thamrin 5',
        lat: '-6.1900',
        lng: '106.8230',
        estimasi_menit: 30,
        jarak_km: '8.1',
        status: 'MENUNGGU' // Belum didatangi
    }
])

const perhentianAktif = ref(daftarPerhentian.value[1]) // Default aktif ke toko ke-2

const pilihPerhentian = (stop) => {
    perhentianAktif.value = stop
}

const badgeStatus = (status) => {
    switch (status) {
        case 'MENUNGGU': return 'bg-slate-200 text-slate-600'
        case 'SAMPAI': return 'bg-blue-100 text-blue-700'
        case 'DITERIMA': return 'bg-emerald-100 text-emerald-700'
        case 'DIRETUR': return 'bg-rose-100 text-rose-700'
        default: return 'bg-slate-100 text-slate-600'
    }
}
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
    width: 6px;
}

.custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 999px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background: #94a3b8;
}
</style>