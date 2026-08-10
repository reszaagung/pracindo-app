<!-- src/features/distribusi/views/CourierDashboard.vue -->
<template>
    <div
        class="flex flex-col w-full min-h-screen bg-slate-50 animate-fade-in relative max-w-md mx-auto shadow-xl border-x border-slate-200">

        <!-- HEADER: Profil & Absensi (Melengkung bergaya Mobile App) -->
        <div class="bg-slate-900 rounded-b-[2.5rem] pt-8 pb-12 px-6 shadow-lg text-white relative overflow-hidden z-10">
            <!-- Ornamen Background -->
            <div class="absolute -right-8 -top-8 w-40 h-40 bg-teal-500/20 rounded-full blur-3xl"></div>

            <div class="flex justify-between items-center relative z-10">
                <div class="flex items-center gap-4">
                    <div
                        class="w-14 h-14 bg-slate-800 rounded-full flex items-center justify-center border-2 border-slate-700 shadow-inner overflow-hidden">
                        <!-- Ganti dengan foto profil user -->
                        <i class="pi pi-user text-2xl text-slate-300"></i>
                    </div>
                    <div>
                        <p class="text-teal-400 text-[10px] font-black uppercase tracking-widest mb-0.5">Kurir Internal
                        </p>
                        <h1 class="text-xl font-bold tracking-tight line-clamp-1">{{ namaKaryawan }}</h1>
                        <p class="text-xs text-slate-400 mt-0.5">{{ idKaryawan }}</p>
                    </div>
                </div>

                <button
                    class="w-10 h-10 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300 hover:text-white transition-colors">
                    <i class="pi pi-bell"></i>
                </button>
            </div>

            <!-- Kartu Absensi Cepat -->
            <div
                class="mt-6 bg-slate-800/80 backdrop-blur-sm border border-slate-700 rounded-2xl p-4 flex items-center justify-between">
                <div>
                    <p class="text-xs text-slate-400 font-medium">Status Kehadiran</p>
                    <p class="text-sm font-bold mt-0.5 flex items-center gap-1.5"
                        :class="isClockedIn ? 'text-emerald-400' : 'text-rose-400'">
                        <i class="pi" :class="isClockedIn ? 'pi-check-circle' : 'pi-times-circle'"></i>
                        {{ isClockedIn ? 'Sedang Bertugas' : 'Belum Absen Masuk' }}
                    </p>
                </div>
                <button @click="toggleAbsen" class="px-5 py-2.5 rounded-xl text-xs font-bold transition-all shadow-md"
                    :class="isClockedIn ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' : 'bg-teal-500 text-white hover:bg-teal-600'">
                    {{ isClockedIn ? 'Akhiri Shift' : 'Absen Masuk' }}
                </button>
            </div>
        </div>

        <!-- KONTEN UTAMA (Digeser naik sedikit agar menumpuk di atas header) -->
        <div class="flex-1 px-5 -mt-6 relative z-20 pb-24">

            <!-- Info Armada Hari Ini -->
            <div v-if="isClockedIn"
                class="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm mb-6 flex items-center justify-between animate-fade-in-up">
                <div class="flex items-center gap-3">
                    <div
                        class="w-10 h-10 bg-slate-100 rounded-xl flex items-center justify-center border border-slate-200">
                        <i class="pi pi-truck text-slate-600"></i>
                    </div>
                    <div>
                        <p class="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-0.5">Armada Anda Hari
                            Ini</p>
                        <h2 class="text-sm font-black text-slate-800">Truk CDD - D 1234 CD</h2>
                    </div>
                </div>
                <button class="text-teal-600 bg-teal-50 px-3 py-1.5 rounded-lg text-xs font-bold">Cek Fisik</button>
            </div>

            <!-- Filter Tugas -->
            <div class="flex items-center justify-between mb-4 mt-2">
                <h3 class="text-base font-bold text-slate-800">Daftar Tugas</h3>
                <div class="bg-slate-200/50 p-1 rounded-lg flex text-[11px] font-bold">
                    <button @click="filterAktif = 'SEMUA'" class="px-3 py-1.5 rounded-md transition-colors"
                        :class="filterAktif === 'SEMUA' ? 'bg-white shadow-sm text-slate-800' : 'text-slate-500'">Semua</button>
                    <button @click="filterAktif = 'DO'" class="px-3 py-1.5 rounded-md transition-colors"
                        :class="filterAktif === 'DO' ? 'bg-white shadow-sm text-slate-800' : 'text-slate-500'">Kirim
                        DO</button>
                    <button @click="filterAktif = 'INTERNAL'" class="px-3 py-1.5 rounded-md transition-colors"
                        :class="filterAktif === 'INTERNAL' ? 'bg-white shadow-sm text-slate-800' : 'text-slate-500'">Internal</button>
                </div>
            </div>

            <!-- List Tugas -->
            <div class="flex flex-col gap-4">
                <div v-for="tugas in tugasTefilter" :key="tugas.id"
                    class="bg-white border border-slate-200 rounded-[20px] p-5 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden">

                    <!-- Garis Indikator Kiri -->
                    <div class="absolute left-0 top-0 bottom-0 w-1.5"
                        :class="getGarisStatus(tugas.status, tugas.jenis)"></div>

                    <div class="flex justify-between items-start mb-3">
                        <div>
                            <div class="flex items-center gap-2 mb-2">
                                <span class="px-2 py-0.5 rounded text-[9px] font-black tracking-widest uppercase border"
                                    :class="getBadgeJenis(tugas.jenis)">
                                    <i class="pi text-[8px] mr-1"
                                        :class="tugas.jenis === 'DO' ? 'pi-box' : 'pi-building'"></i> {{ tugas.jenis }}
                                </span>
                                <span class="text-[10px] font-bold text-slate-400"><i
                                        class="pi pi-clock text-[9px]"></i> {{ tugas.jam }}</span>
                            </div>
                            <h2 class="text-base font-black text-slate-800">{{ tugas.nomor }}</h2>
                        </div>
                        <span class="px-2.5 py-1 rounded-md text-[10px] font-black tracking-widest uppercase border"
                            :class="getBadgeStatus(tugas.status)">
                            {{ tugas.status }}
                        </span>
                    </div>

                    <div class="bg-slate-50 p-3 rounded-xl border border-slate-100 mb-4">
                        <div class="mb-2">
                            <span
                                class="text-[9px] font-bold text-slate-400 uppercase tracking-wider block mb-0.5">Tujuan</span>
                            <p class="text-sm font-bold text-slate-700 leading-tight">{{ tugas.tujuan_nama }}</p>
                        </div>
                        <div>
                            <span
                                class="text-[9px] font-bold text-slate-400 uppercase tracking-wider block mb-0.5">Alamat
                                / Catatan</span>
                            <p class="text-xs text-slate-600 line-clamp-2">{{ tugas.tujuan_alamat }}</p>
                        </div>
                    </div>

                    <!-- Tombol Aksi dinamis (Hanya aktif jika sudah absen masuk) -->
                    <div class="flex gap-2">
                        <button v-if="!isClockedIn" disabled
                            class="flex-1 py-3 bg-slate-100 text-slate-400 text-xs font-bold rounded-xl cursor-not-allowed border border-slate-200">
                            Absen Masuk Dahulu
                        </button>
                        <template v-else>
                            <button v-if="tugas.status === 'SIAP JALAN'" @click="tugas.status = 'OTW'"
                                class="flex-1 py-3 bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold rounded-xl shadow-md transition-colors flex justify-center items-center gap-2">
                                <i class="pi pi-play text-[10px]"></i> Mulai Jalan
                            </button>
                            <button v-if="tugas.status === 'OTW'" @click="tugas.status = 'SAMPAI'"
                                class="flex-1 py-3 bg-amber-500 hover:bg-amber-600 text-white text-xs font-bold rounded-xl shadow-md transition-colors flex justify-center items-center gap-2">
                                <i class="pi pi-map-marker text-[10px]"></i> Tiba di Lokasi
                            </button>
                            <button v-if="tugas.status === 'SAMPAI'" @click="selesaikanTugas(tugas)"
                                class="flex-1 py-3 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-xl shadow-md transition-colors flex justify-center items-center gap-2">
                                <i class="pi pi-camera text-[10px]"></i> Upload Bukti (POD)
                            </button>
                            <div v-if="tugas.status === 'SELESAI'"
                                class="flex-1 py-2.5 bg-emerald-50 border border-emerald-100 text-emerald-600 text-xs font-bold rounded-xl flex justify-center items-center gap-1.5 cursor-default">
                                <i class="pi pi-check-circle text-emerald-500"></i> Tugas Selesai
                            </div>
                        </template>

                        <!-- Tombol Maps -->
                        <button
                            class="w-12 h-12 flex-shrink-0 rounded-xl bg-blue-50 text-blue-600 border border-blue-100 hover:bg-blue-100 flex items-center justify-center transition-colors">
                            <i class="pi pi-map"></i>
                        </button>
                    </div>
                </div>
            </div>

            <div v-if="tugasTefilter.length === 0" class="py-12 flex flex-col items-center text-center">
                <i class="pi pi-check-square text-4xl text-slate-300 mb-3"></i>
                <p class="text-sm font-bold text-slate-800">Tidak Ada Tugas</p>
                <p class="text-xs text-slate-500 mt-1">Anda sudah menyelesaikan semua tugas di kategori ini.</p>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed } from 'vue'

// Data Profil Internal
const namaKaryawan = ref('Jajang Mulyana')
const idKaryawan = ref('EMP-2023-089')
const isClockedIn = ref(false)

// State Filter
const filterAktif = ref('SEMUA')

// Data Tugas Karyawan (Campuran Eksternal dan Internal)
const daftarTugas = ref([
    {
        id: 1,
        jenis: 'DO', // Delivery Order ke Kustomer
        nomor: 'DO-202608-001',
        jam: '08:30 WIB',
        tujuan_nama: 'PT. Mitra Bangunan Sejahtera',
        tujuan_alamat: 'Jl. Raya Industri Km 14, Bekasi (Titip di Satpam Depan)',
        status: 'SIAP JALAN'
    },
    {
        id: 2,
        jenis: 'INTERNAL', // Tugas Perusahaan
        nomor: 'TGS-INT-099',
        jam: '13:00 WIB',
        tujuan_nama: 'Kantor Pusat Pracindo (Finance)',
        tujuan_alamat: 'Ambil berkas tagihan faktur pajak untuk dibawa ke Gudang Utama.',
        status: 'SIAP JALAN'
    },
    {
        id: 3,
        jenis: 'DO',
        nomor: 'DO-202608-003',
        jam: '15:15 WIB',
        tujuan_nama: 'Toko Besi Makmur',
        tujuan_alamat: 'Jl. Ahmad Yani No 45, Sidoarjo',
        status: 'SELESAI'
    }
])

const tugasTefilter = computed(() => {
    if (filterAktif.value === 'SEMUA') return daftarTugas.value
    return daftarTugas.value.filter(t => t.jenis === filterAktif.value)
})

// Logika UI & Aksi
const toggleAbsen = () => {
    if (isClockedIn.value) {
        if (confirm('Apakah Anda yakin ingin mengakhiri shift hari ini?')) {
            isClockedIn.value = false
        }
    } else {
        isClockedIn.value = true
        alert('Berhasil absen masuk! Hati-hati di jalan.')
    }
}

const selesaikanTugas = (tugas) => {
    // Di aplikasi asli, ini akan membuka modal kamera/upload seperti di komponen CourierTask sebelumnya
    tugas.status = 'SELESAI'
    alert(`Upload bukti berhasil. Tugas ${tugas.nomor} dinyatakan selesai!`)
}

// Styling Dinamis
const getBadgeJenis = (jenis) => {
    return jenis === 'DO'
        ? 'bg-blue-50 text-blue-600 border-blue-200'
        : 'bg-teal-50 text-teal-600 border-teal-200'
}

const getBadgeStatus = (status) => {
    switch (status) {
        case 'SIAP JALAN': return 'bg-slate-100 text-slate-500 border-slate-200'
        case 'OTW': return 'bg-amber-50 text-amber-600 border-amber-200'
        case 'SAMPAI': return 'bg-blue-50 text-blue-600 border-blue-200'
        case 'SELESAI': return 'bg-emerald-50 text-emerald-600 border-emerald-200'
        default: return 'bg-slate-50 text-slate-500 border-slate-200'
    }
}

const getGarisStatus = (status, jenis) => {
    if (status === 'SELESAI') return 'bg-emerald-500'
    return jenis === 'DO' ? 'bg-blue-500' : 'bg-teal-500'
}
</script>

<style scoped>
.animate-fade-in {
    animation: fadeIn 0.4s ease-out forwards;
}

.animate-fade-in-up {
    animation: fadeInUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

@keyframes fadeIn {
    from {
        opacity: 0;
    }

    to {
        opacity: 1;
    }
}

@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* Membatasi lebar maksimal agar tidak aneh saat dibuka di monitor komputer besar */
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