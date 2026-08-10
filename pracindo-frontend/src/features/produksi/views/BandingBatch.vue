<!--
  features/produksi/views/BandingBatch.vue
  =========================================
  DESKTOP-FIRST. Parameter sebagai BARIS, batch sebagai KOLOM.

  Ini layar tempat "kenapa batch A jadi dan B tidak" terjawab. Karena itu
  baris yang nilainya SAMA di semua batch diredupkan, dan yang BERBEDA
  diberi latar — mata harus langsung jatuh ke selisihnya tanpa membaca
  angka satu per satu. Kalau selisihnya tidak langsung terlihat, layar ini
  gagal walaupun datanya benar.

  Bahan dinormalkan per unit hasil (§D), supaya batch 5 kg dan 3 kg tetap
  sebanding.

  Mobile: TIDAK memaksa tabel lebar ke layar kecil — satu kartu per batch.
-->
<template>
    <div class="flex flex-col w-full animate-fade-in">
        <div class="mb-4 md:mb-6">
            <p class="text-xs text-slate-400 mb-1">
                <router-link :to="{ name: 'produksi-sesi-list' }" class="hover:text-slate-700 transition-colors">
                    Sesi Produksi</router-link> › Banding Batch
            </p>
            <h2 class="text-xl md:text-2xl font-bold text-slate-800 tracking-tight">Banding Batch</h2>
            <p class="text-xs text-slate-500 mt-1">
                Pilih 2–8 sesi untuk dibandingkan berdampingan.
            </p>
        </div>

        <!-- Pemilih sesi -->
        <div class="bg-white border border-slate-200 rounded-[24px] p-4 md:p-6 shadow-sm mb-4">
            <div class="flex justify-between items-center mb-3 flex-wrap gap-2">
                <div>
                    <h3 class="text-sm font-bold text-slate-800">Pilih Sesi</h3>
                    <p class="text-xs text-slate-500">{{ dipilih.length }} dari maksimal {{ MAKS }} terpilih</p>
                </div>
                <button type="button" @click="bandingkan" :disabled="dipilih.length < 2 || sedangProses"
                    class="px-4 py-2 bg-slate-900 hover:bg-slate-800 disabled:opacity-40 text-white text-xs font-bold rounded-xl transition-colors">
                    <i v-if="sedangProses" class="pi pi-spin pi-spinner mr-1"></i>
                    Bandingkan
                </button>
            </div>

            <div class="flex flex-wrap gap-2">
                <button type="button" v-for="s in daftarSesi" :key="s.id" @click="toggle(s.id)"
                    :disabled="!dipilih.includes(s.id) && dipilih.length >= MAKS"
                    :class="dipilih.includes(s.id)
                        ? 'bg-slate-900 text-white border-slate-900'
                        : 'bg-white text-slate-600 border-slate-200 hover:border-slate-400 disabled:opacity-30'"
                    class="px-3 py-2 rounded-xl border text-xs font-bold transition-colors text-left">
                    {{ s.nomor.split('/').slice(-2).join('/') }}
                    <span class="block font-normal opacity-70 text-[10px]">
                        {{ s.produk_jadi_kode }} · {{ s.jenis_sesi === 'RND' ? 'R&D' : 'Rutin' }} · {{ s.status }}
                    </span>
                </button>
            </div>
        </div>

        <p v-if="galat" class="mb-4 px-4 py-3 bg-red-50 text-red-600 rounded-xl text-xs">{{ galat }}</p>

        <template v-if="banding">
            <!-- ============ DESKTOP: matriks ============ -->
            <div class="hidden md:block bg-white border border-slate-200 rounded-[24px] p-4 md:p-6 shadow-sm">
                <div class="flex items-center gap-4 mb-4 pb-4 border-b border-slate-100 flex-wrap">
                    <h3 class="text-sm font-bold text-slate-800">Matriks Perbandingan</h3>
                    <div class="flex items-center gap-3 text-[10px] text-slate-500">
                        <span class="flex items-center gap-1">
                            <span class="w-3 h-3 rounded bg-amber-50 border border-amber-200"></span> berbeda antar batch
                        </span>
                        <span class="flex items-center gap-1">
                            <span class="w-3 h-3 rounded bg-white border border-slate-200"></span> sama di semua batch
                        </span>
                    </div>
                </div>

                <div class="overflow-x-auto custom-scrollbar">
                    <table class="w-full text-left text-xs border-collapse">
                        <thead>
                            <tr>
                                <th class="py-3 px-3 font-semibold text-slate-500 sticky left-0 bg-white z-10 min-w-[11rem]">
                                    Parameter
                                </th>
                                <th v-for="s in banding.sesi" :key="s.id"
                                    class="py-3 px-3 font-semibold text-slate-700 min-w-[9rem] align-top">
                                    <router-link :to="{ name: 'produksi-sesi-detail', params: { id: s.id } }"
                                        class="font-bold text-slate-800 hover:underline block">
                                        {{ s.nomor.split('/').slice(-2).join('/') }}
                                    </router-link>
                                    <span class="block text-[10px] font-normal text-slate-400 mt-0.5">
                                        {{ tanggal(s.tanggal) }} · {{ s.status }}
                                    </span>
                                </th>
                            </tr>
                        </thead>

                        <tbody>
                            <!-- Hasil -->
                            <tr class="bg-slate-50">
                                <td colspan="99" class="py-1.5 px-3 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                                    Hasil
                                </td>
                            </tr>
                            <tr v-for="r in barisHasil" :key="r.label" class="border-b border-slate-100">
                                <td class="py-2.5 px-3 font-semibold sticky left-0 bg-white z-10"
                                    :class="r.berbeda ? 'text-slate-800' : 'text-slate-400'">
                                    {{ r.label }}
                                </td>
                                <td v-for="(v, i) in r.nilai" :key="i" class="py-2.5 px-3 tabular-nums"
                                    :class="kelasSel(r, i)">
                                    {{ v ?? '—' }}
                                </td>
                            </tr>

                            <!-- Pengukuran -->
                            <tr class="bg-slate-50">
                                <td colspan="99" class="py-1.5 px-3 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                                    Pengukuran
                                </td>
                            </tr>
                            <tr v-for="r in barisPengukuran" :key="r.label" class="border-b border-slate-100">
                                <td class="py-2.5 px-3 font-semibold sticky left-0 bg-white z-10"
                                    :class="r.berbeda ? 'text-slate-800' : 'text-slate-400'">
                                    {{ r.label }}
                                    <span v-if="r.satuan" class="font-normal text-slate-400">({{ r.satuan }})</span>
                                    <span v-if="r.tahap === 'UJI'"
                                        class="ml-1 px-1 py-0.5 rounded bg-sky-50 text-sky-700 text-[9px] font-bold border border-sky-200">UJI</span>
                                </td>
                                <td v-for="(v, i) in r.nilai" :key="i" class="py-2.5 px-3 tabular-nums"
                                    :class="kelasSel(r, i)">
                                    {{ v ?? '—' }}
                                </td>
                            </tr>
                            <tr v-if="barisPengukuran.length === 0">
                                <td :colspan="banding.sesi.length + 1" class="py-4 px-3 text-slate-400">
                                    Tidak ada pengukuran tercatat di sesi terpilih.
                                </td>
                            </tr>

                            <!-- Bahan per unit -->
                            <tr class="bg-slate-50">
                                <td colspan="99" class="py-1.5 px-3 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                                    Bahan per unit hasil
                                </td>
                            </tr>
                            <tr v-for="r in barisBahan" :key="r.label" class="border-b border-slate-100">
                                <td class="py-2.5 px-3 font-semibold sticky left-0 bg-white z-10"
                                    :class="r.berbeda ? 'text-slate-800' : 'text-slate-400'">
                                    {{ r.label }}
                                    <span v-if="r.satuan" class="font-normal text-slate-400">({{ r.satuan }}/unit)</span>
                                </td>
                                <td v-for="(v, i) in r.nilai" :key="i" class="py-2.5 px-3 tabular-nums"
                                    :class="kelasSel(r, i)">
                                    {{ v ?? '—' }}
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <p class="mt-4 text-[11px] text-slate-400">
                    Pengukuran yang dicatat berulang diwakili nilai TERAKHIR di sesi itu.
                </p>
            </div>

            <!-- ============ MOBILE: satu kartu per batch ============ -->
            <div class="md:hidden">
                <p class="mb-3 px-4 py-3 bg-slate-100 text-slate-600 rounded-2xl text-xs leading-relaxed">
                    <i class="pi pi-info-circle mr-1"></i>
                    Matriks berdampingan butuh layar lebar. Di sini batch ditampilkan satu per kartu —
                    geser untuk membandingkan.
                </p>

                <div class="flex gap-3 overflow-x-auto custom-scrollbar snap-x snap-mandatory -mx-4 px-4 pb-2">
                    <div v-for="(s, i) in banding.sesi" :key="s.id"
                        class="snap-center shrink-0 w-[85vw] bg-white border border-slate-200 rounded-[24px] p-4 shadow-sm">
                        <router-link :to="{ name: 'produksi-sesi-detail', params: { id: s.id } }"
                            class="font-bold text-slate-800 text-sm hover:underline">
                            {{ s.nomor }}
                        </router-link>
                        <p class="text-xs text-slate-500 mb-3">{{ tanggal(s.tanggal) }} · {{ s.status }}</p>

                        <template v-for="(kel, ki) in [
                            { judul: 'Hasil', baris: barisHasil },
                            { judul: 'Pengukuran', baris: barisPengukuran },
                            { judul: 'Bahan per unit', baris: barisBahan },
                        ]" :key="ki">
                            <p class="text-[10px] font-bold text-slate-400 uppercase tracking-wider mt-3 mb-1">
                                {{ kel.judul }}
                            </p>
                            <div v-for="r in kel.baris" :key="r.label"
                                class="flex justify-between items-center py-1.5 border-b border-slate-100 last:border-0"
                                :class="r.berbeda ? '' : 'opacity-40'">
                                <span class="text-xs text-slate-600">
                                    {{ r.label }}
                                    <span v-if="r.satuan" class="text-slate-400">({{ r.satuan }})</span>
                                </span>
                                <span class="text-xs font-bold tabular-nums"
                                    :class="r.berbeda ? 'text-amber-700' : 'text-slate-500'">
                                    {{ r.nilai[i] ?? '—' }}
                                </span>
                            </div>
                        </template>
                    </div>
                </div>
            </div>
        </template>

        <div v-else-if="!sedangProses"
            class="bg-white border border-slate-200 rounded-[24px] p-10 shadow-sm text-center">
            <div class="w-12 h-12 bg-slate-50 rounded-full flex items-center justify-center mb-3 mx-auto">
                <i class="pi pi-chart-bar text-slate-400 text-xl"></i>
            </div>
            <h4 class="text-sm font-bold text-slate-800 mb-1">Belum ada yang dibandingkan</h4>
            <p class="text-xs text-slate-500">Pilih minimal dua sesi di atas, lalu tekan Bandingkan.</p>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useSesiProduksi } from '../composables/useSesiProduksi'
import { tanggal, angka } from '@/utils/format'

const MAKS = 8

const route = useRoute()
const router = useRouter()
const { daftarSesi, banding, sedangProses, galat, muatSesi, muatBanding } = useSesiProduksi()

const dipilih = ref([])

const toggle = (id) => {
    const i = dipilih.value.indexOf(id)
    if (i >= 0) dipilih.value.splice(i, 1)
    else if (dipilih.value.length < MAKS) dipilih.value.push(id)
}

const bandingkan = async () => {
    // ids ikut ke URL supaya perbandingan bisa dikirim ke orang lain apa adanya.
    router.replace({ name: 'produksi-banding', query: { ids: dipilih.value.join(',') } })
    await muatBanding(dipilih.value)
}

/**
 * Sebuah baris "berbeda" kalau nilainya tidak seragam di semua batch.
 * Nilai kosong ikut dihitung sebagai perbedaan — batch yang TIDAK mencatat
 * suatu parameter adalah temuan tersendiri, bukan sekadar data hilang.
 */
const tandai = (label, nilai, extra = {}) => ({
    label, nilai, ...extra,
    berbeda: new Set(nilai.map((v) => (v === null || v === undefined ? '∅' : String(v)))).size > 1,
})

const barisHasil = computed(() => {
    if (!banding.value) return []
    const s = banding.value.sesi
    return [
        tandai('Jenis sesi', s.map((x) => (x.jenis_sesi === 'RND' ? 'R&D' : 'Rutin'))),
        tandai('Status', s.map((x) => x.status)),
        tandai('Produk', s.map((x) => x.produk_jadi_kode)),
        tandai('Qty target', s.map((x) => angka(x.qty_target, 3)), { satuan: s[0]?.satuan_kode }),
        tandai('Qty hasil', s.map((x) => angka(x.qty_hasil, 3)), { satuan: s[0]?.satuan_kode }),
        tandai('Rendemen', s.map((x) => `${(parseFloat(x.rendemen || 0) * 100).toFixed(1)}%`)),
    ]
})

const barisPengukuran = computed(() =>
    (banding.value?.pengukuran ?? []).map((p) =>
        tandai(p.label, p.nilai.map((v) => (v === null ? null : v)), {
            satuan: p.satuan, tahap: p.tahap, numerik: true,
        })))

const barisBahan = computed(() =>
    (banding.value?.bahan_per_unit ?? []).map((b) =>
        tandai(b.label, b.nilai.map((v) => (v === null ? null : v)), {
            satuan: b.satuan, numerik: true,
        })))

/**
 * Sel di baris yang berbeda diberi latar. Untuk baris numerik, nilai
 * tertinggi dan terendah ditebalkan — itu yang biasanya jadi tersangka
 * pertama saat menjelaskan kenapa satu batch berbeda.
 */
const kelasSel = (r, i) => {
    if (!r.berbeda) return 'text-slate-400'
    const dasar = 'bg-amber-50 text-slate-800'
    if (!r.numerik) return dasar

    const angkaSaja = r.nilai.map((v) => parseFloat(v)).filter((n) => !Number.isNaN(n))
    if (angkaSaja.length < 2) return dasar

    const n = parseFloat(r.nilai[i])
    if (Number.isNaN(n)) return dasar
    if (n === Math.max(...angkaSaja)) return `${dasar} font-black text-amber-800`
    if (n === Math.min(...angkaSaja)) return `${dasar} font-black text-blue-700`
    return dasar
}

onMounted(async () => {
    await muatSesi()
    const dariUrl = String(route.query.ids ?? '').split(',').filter(Boolean).map(Number)
    if (dariUrl.length >= 2) {
        dipilih.value = dariUrl.slice(0, MAKS)
        await muatBanding(dipilih.value)
    }
})
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
    height: 6px;
}

.custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 4px;
}
</style>
