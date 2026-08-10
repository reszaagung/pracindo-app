<!--
  features/produksi/views/SesiList.vue
  =====================================
  Daftar sesi. Desktop tabel, mobile kartu — bukan tabel yang digeser.

  RND vs PRODUKSI dibedakan LENCANA BERTEKS, bukan warna saja. Layar ini
  dibaca di gudang dengan cahaya buruk dan sebagian orang tidak membedakan
  merah-hijau; warna saja bukan pembeda yang bisa diandalkan.
-->
<template>
    <div class="flex flex-col w-full animate-fade-in">
        <!-- Header -->
        <div class="mb-4 md:mb-6 flex justify-between items-end gap-3 flex-wrap">
            <div>
                <p class="text-xs text-slate-400 mb-1">
                    <router-link :to="{ name: 'produksi-sesi-list' }" class="hover:text-slate-700 transition-colors">
                        Portal Produksi</router-link> › Sesi
                </p>
                <h2 class="text-xl md:text-2xl font-bold text-slate-800 tracking-tight">Sesi Produksi</h2>
            </div>

            <div class="flex items-center gap-2">
                <router-link :to="{ name: 'produksi-banding' }"
                    class="px-4 py-2 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-bold rounded-xl transition-colors flex items-center gap-2 shadow-sm">
                    <i class="pi pi-chart-bar"></i> Banding Batch
                </router-link>
                <router-link :to="{ name: 'produksi-sesi-buat' }"
                    class="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold rounded-xl transition-colors flex items-center gap-2 shadow-sm transform hover:-translate-y-0.5">
                    <i class="pi pi-plus"></i> Sesi Baru
                </router-link>
            </div>
        </div>

        <!-- Kartu statistik -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div class="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm">
                <p class="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">SEDANG BERJALAN</p>
                <h3 class="text-2xl font-black text-slate-800">{{ statistik.berjalan }}</h3>
                <p class="text-xs text-slate-500 mt-2">Bahan sudah keluar dari pool</p>
            </div>
            <div class="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm">
                <p class="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">SELESAI BULAN INI</p>
                <h3 class="text-2xl font-black text-slate-800">{{ statistik.selesai }}</h3>
                <p class="text-xs text-slate-500 mt-2">Hasil sudah tercatat</p>
            </div>
            <div class="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm">
                <p class="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">GAGAL BULAN INI</p>
                <h3 class="text-2xl font-black text-slate-800">{{ statistik.gagal }}</h3>
                <p class="text-xs text-slate-500 mt-2">Kerugian sudah dibebankan</p>
            </div>
        </div>

        <div class="bg-white border border-slate-200 rounded-[24px] p-4 md:p-6 shadow-sm w-full min-h-[400px]">
            <div
                class="flex flex-col xl:flex-row justify-between items-start xl:items-center gap-4 mb-6 pb-4 border-b border-slate-100">
                <div>
                    <h3 class="text-sm font-bold text-slate-800">Daftar Sesi</h3>
                    <p class="text-xs text-slate-500">Terbaru di atas</p>
                </div>

                <div class="flex flex-col md:flex-row items-center gap-3 w-full xl:w-auto">
                    <div class="relative w-full md:w-64">
                        <i class="pi pi-search absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-xs"></i>
                        <input type="text" v-model="cari" placeholder="Cari nomor / produk"
                            class="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-slate-900 text-slate-700" />
                    </div>

                    <div class="flex bg-slate-50 p-1 rounded-xl w-full md:w-auto overflow-x-auto custom-scrollbar">
                        <button v-for="tab in TAB" :key="tab"
                            @click="saringStatus = tab"
                            :class="saringStatus === tab ? 'bg-white text-slate-800 shadow-[0_2px_8px_rgba(0,0,0,0.04)] font-bold' : 'text-slate-500 hover:text-slate-700'"
                            class="px-3 py-1.5 text-xs rounded-lg transition-all whitespace-nowrap capitalize">
                            {{ tab.toLowerCase() }}
                        </button>
                    </div>
                </div>
            </div>

            <p v-if="galat" class="mb-4 px-4 py-3 bg-red-50 text-red-600 rounded-xl text-xs">{{ galat }}</p>

            <div v-if="sedangProses" class="flex flex-col items-center justify-center py-12 text-center">
                <i class="pi pi-spin pi-spinner text-slate-300 text-2xl mb-3"></i>
                <p class="text-xs text-slate-500">Memuat data...</p>
            </div>

            <div v-else-if="tampil.length === 0" class="flex flex-col items-center justify-center py-12 text-center">
                <div class="w-12 h-12 bg-slate-50 rounded-full flex items-center justify-center mb-3">
                    <i class="pi pi-inbox text-slate-400 text-xl"></i>
                </div>
                <h4 class="text-sm font-bold text-slate-800 mb-1">Tidak ada sesi yang cocok</h4>
                <p class="text-xs text-slate-500">Ubah kata kunci pencarian atau tab status.</p>
            </div>

            <template v-else>
                <!-- Desktop -->
                <div class="hidden md:block overflow-x-auto">
                    <table class="w-full text-left text-sm">
                        <thead class="text-slate-500 bg-slate-50/50">
                            <tr>
                                <th class="py-3 px-4 font-semibold rounded-tl-xl">Nomor</th>
                                <th class="py-3 px-4 font-semibold">Jenis</th>
                                <th class="py-3 px-4 font-semibold">Tanggal</th>
                                <th class="py-3 px-4 font-semibold">Produk</th>
                                <th class="py-3 px-4 font-semibold text-right">Target</th>
                                <th class="py-3 px-4 font-semibold text-right">Hasil</th>
                                <th class="py-3 px-4 font-semibold text-center rounded-tr-xl">Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="s in tampil" :key="s.id" @click="buka(s)"
                                class="border-b border-slate-100 hover:bg-slate-50/50 transition-colors cursor-pointer">
                                <td class="py-3 px-4 font-bold text-slate-800">{{ s.nomor }}</td>
                                <td class="py-3 px-4">
                                    <span :class="kelasJenis(s.jenis_sesi)"
                                        class="px-2 py-1 rounded-lg text-[10px] font-bold tracking-wide border">
                                        {{ s.jenis_sesi === 'RND' ? 'R&D' : 'RUTIN' }}
                                    </span>
                                </td>
                                <td class="py-3 px-4 text-slate-600">{{ tanggal(s.tanggal) }}</td>
                                <td class="py-3 px-4 text-slate-700">
                                    {{ s.produk_jadi_kode }}
                                    <span v-if="!s.hasil_masuk_pool"
                                        class="ml-1 text-[10px] font-bold text-amber-700">· non-stok</span>
                                </td>
                                <td class="py-3 px-4 text-right text-slate-600">
                                    {{ angka(s.qty_target, 3) }} {{ s.satuan_kode }}
                                </td>
                                <td class="py-3 px-4 text-right font-semibold text-slate-800">
                                    {{ angka(s.qty_hasil, 3) }}
                                </td>
                                <td class="py-3 px-4 text-center">
                                    <span :class="kelasStatus(s.status)"
                                        class="px-2.5 py-1 rounded-full text-[10px] font-bold tracking-wide uppercase">
                                        {{ s.status }}
                                    </span>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <!-- Mobile -->
                <div class="md:hidden flex flex-col gap-3">
                    <button v-for="s in tampil" :key="s.id" @click="buka(s)"
                        class="text-left bg-white border border-slate-200 rounded-2xl p-4 active:bg-slate-50 transition-colors">
                        <div class="flex justify-between items-start gap-2 mb-2">
                            <span class="font-bold text-slate-800 text-sm">{{ s.nomor }}</span>
                            <span :class="kelasStatus(s.status)"
                                class="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase shrink-0">
                                {{ s.status }}
                            </span>
                        </div>
                        <div class="flex items-center gap-2 mb-2">
                            <span :class="kelasJenis(s.jenis_sesi)"
                                class="px-2 py-0.5 rounded-lg text-[10px] font-bold border">
                                {{ s.jenis_sesi === 'RND' ? 'R&D' : 'RUTIN' }}
                            </span>
                            <span v-if="!s.hasil_masuk_pool"
                                class="px-2 py-0.5 rounded-lg text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200">
                                TIDAK MASUK STOK
                            </span>
                        </div>
                        <p class="text-xs text-slate-500">
                            {{ s.produk_jadi_nama }} · {{ tanggal(s.tanggal) }}
                        </p>
                        <p class="text-xs text-slate-600 mt-1">
                            Target {{ angka(s.qty_target, 3) }} {{ s.satuan_kode }} ·
                            Hasil <span class="font-semibold text-slate-800">{{ angka(s.qty_hasil, 3) }}</span>
                        </p>
                    </button>
                </div>
            </template>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useSesiProduksi } from '../composables/useSesiProduksi'
import { tanggal, angka } from '@/utils/format'

const TAB = ['SEMUA', 'DRAFT', 'BERJALAN', 'SELESAI', 'GAGAL', 'BATAL']

const router = useRouter()
const { daftarSesi, sedangProses, galat, muatSesi } = useSesiProduksi()

const cari = ref('')
const saringStatus = ref('SEMUA')

const tampil = computed(() => {
    const q = cari.value.trim().toLowerCase()
    return daftarSesi.value.filter((s) => {
        const cocokStatus = saringStatus.value === 'SEMUA' || s.status === saringStatus.value
        const cocokCari = !q
            || s.nomor.toLowerCase().includes(q)
            || (s.produk_jadi_kode ?? '').toLowerCase().includes(q)
            || (s.produk_jadi_nama ?? '').toLowerCase().includes(q)
        return cocokStatus && cocokCari
    })
})

const bulanIni = (iso) => {
    const d = new Date(iso)
    const n = new Date()
    return d.getMonth() === n.getMonth() && d.getFullYear() === n.getFullYear()
}

const statistik = computed(() => ({
    berjalan: daftarSesi.value.filter((s) => s.status === 'BERJALAN').length,
    selesai: daftarSesi.value.filter((s) => s.status === 'SELESAI' && bulanIni(s.tanggal)).length,
    gagal: daftarSesi.value.filter((s) => s.status === 'GAGAL' && bulanIni(s.tanggal)).length,
}))

/**
 * Sesi BERJALAN dibuka ke layar kerja, bukan detail — orang yang mengetuk
 * sesi berjalan hampir selalu mau mencatat sesuatu, bukan membaca arsip.
 */
const buka = (s) => router.push(
    s.status === 'BERJALAN'
        ? { name: 'produksi-sesi-berjalan', params: { id: s.id } }
        : { name: 'produksi-sesi-detail', params: { id: s.id } },
)

const kelasJenis = (j) => j === 'RND'
    ? 'bg-violet-50 text-violet-700 border-violet-200'
    : 'bg-slate-50 text-slate-600 border-slate-200'

const kelasStatus = (st) => ({
    DRAFT: 'bg-slate-100 text-slate-600',
    BERJALAN: 'bg-blue-50 text-blue-600',
    SELESAI: 'bg-emerald-50 text-emerald-600',
    GAGAL: 'bg-red-50 text-red-600',
    BATAL: 'bg-slate-100 text-slate-500',
}[st] ?? 'bg-slate-100 text-slate-600')

onMounted(() => muatSesi())
</script>

<style scoped>
.animate-fade-in {
    animation: fadeIn 0.3s ease-out forwards;
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

.custom-scrollbar::-webkit-scrollbar {
    height: 4px;
}

.custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 4px;
}
</style>
