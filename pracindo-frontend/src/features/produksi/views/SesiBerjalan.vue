<!--
  features/produksi/views/SesiBerjalan.vue
  =========================================
  MOBILE-FIRST. Layar ini dipakai sambil berdiri di dekat tangki, satu
  tangan memegang HP.

  TARGET: DUA KETUKAN PER PENGUKURAN.
    ketukan 1  pilih jenis dari katalog (chip, terakhir-dipakai di depan)
    ketik      angka
    ketukan 2  Simpan
  Satuan ikut otomatis dari JenisPengukuran, waktu diisi server. Tidak ada
  dropdown bebas-teks — kalau operator boleh mengetik "suhu" atau "Suhu"
  sesuka hati, arsipnya tidak bisa dibandingkan antar batch.

  Kalau mencatat suhu butuh lima ketukan, orang akan mencatat di kertas dan
  mengisi belakangan dari ingatan — dan seluruh premis "batch bisa
  direproduksi" runtuh. Itu sebabnya panel input MENEMPEL di bawah layar
  (thumb zone) dan lini masa tetap terlihat di belakangnya.
-->
<template>
    <div class="pb-[19rem] lg:pb-0 animate-fade-in">
        <!-- Kepala -->
        <div class="sticky top-0 z-20 -mx-4 md:-mx-6 px-4 md:px-6 py-3 bg-slate-50/95 backdrop-blur
                    border-b border-slate-200">
            <div class="flex items-center justify-between gap-3">
                <div class="min-w-0">
                    <p class="text-xs text-slate-400 truncate">
                        <router-link :to="{ name: 'produksi-sesi-list' }" class="hover:text-slate-700">Sesi</router-link>
                        › Berjalan
                    </p>
                    <h2 class="text-base md:text-xl font-bold text-slate-800 truncate">
                        {{ sesi?.nomor ?? '—' }}
                    </h2>
                    <p class="text-xs text-slate-500 truncate">
                        {{ sesi?.produk_jadi_nama }} · target
                        {{ angka(sesi?.qty_target, 3) }} {{ sesi?.satuan_kode }}
                    </p>
                </div>

                <div class="text-right shrink-0">
                    <p class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Berjalan</p>
                    <p class="text-xl md:text-2xl font-black text-slate-800 tabular-nums">{{ jamBerjalan }}</p>
                    <span v-if="sesi" :class="sesi.jenis_sesi === 'RND'
                        ? 'bg-violet-50 text-violet-700 border-violet-200'
                        : 'bg-slate-100 text-slate-600 border-slate-200'"
                        class="inline-block mt-1 px-2 py-0.5 rounded-lg text-[10px] font-bold border">
                        {{ sesi.jenis_sesi === 'RND' ? 'R&D' : 'RUTIN' }}
                    </span>
                </div>
            </div>
        </div>

        <p v-if="galat" class="mt-4 px-4 py-3 bg-red-50 text-red-600 rounded-xl text-xs whitespace-pre-line">
            {{ galat }}
        </p>

        <div class="lg:grid lg:grid-cols-[1fr_22rem] lg:gap-6 lg:items-start mt-4">
            <!-- ============ LINI MASA ============ -->
            <div class="bg-white border border-slate-200 rounded-[24px] p-4 md:p-5 shadow-sm">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-sm font-bold text-slate-800">Lini Masa</h3>
                    <p class="text-xs text-slate-500">{{ liniMasa.length }} entri · terbaru di atas</p>
                </div>

                <p v-if="liniMasa.length === 0" class="py-10 text-center text-xs text-slate-400">
                    Belum ada yang dicatat. Mulai dari panel di bawah.
                </p>

                <ul class="flex flex-col gap-2">
                    <li v-for="b in liniMasa" :key="b.kunci"
                        :class="b.digantikan ? 'opacity-50' : ''"
                        class="border border-slate-100 rounded-2xl p-3 bg-slate-50/50">
                        <!-- Pengukuran -->
                        <template v-if="b.jenis === 'ukur'">
                            <div class="flex justify-between items-start gap-2">
                                <div class="min-w-0">
                                    <p class="text-xs font-bold text-slate-800">
                                        {{ b.data.nama_label }}
                                        <span v-if="b.data.tahap === 'UJI'"
                                            class="ml-1 px-1.5 py-0.5 rounded bg-sky-50 text-sky-700 text-[9px] font-bold border border-sky-200">
                                            UJI
                                        </span>
                                        <span v-if="b.data.mengoreksi"
                                            class="ml-1 px-1.5 py-0.5 rounded bg-amber-50 text-amber-700 text-[9px] font-bold border border-amber-200">
                                            KOREKSI
                                        </span>
                                    </p>
                                    <p v-if="b.data.catatan" class="text-[11px] text-slate-500 mt-0.5">
                                        {{ b.data.catatan }}
                                    </p>
                                </div>
                                <p class="text-sm font-black text-slate-800 shrink-0 tabular-nums">
                                    {{ b.data.nilai !== null ? angka(b.data.nilai, 2) : b.data.nilai_teks }}
                                    <span class="text-[10px] font-bold text-slate-400">{{ b.data.satuan }}</span>
                                </p>
                            </div>
                            <div class="flex justify-between items-center mt-1.5">
                                <p class="text-[10px] text-slate-400">
                                    {{ tanggalJam(b.data.waktu) }} · {{ b.data.dicatat_oleh_nama }}
                                    <span v-if="b.digantikan" class="font-bold text-amber-600">· sudah dikoreksi</span>
                                </p>
                                <!-- Append-only: tidak ada edit/hapus. Koreksi = entri baru. -->
                                <button v-if="!b.digantikan" type="button" @click="mulaiKoreksi(b.data)"
                                    class="text-[10px] font-bold text-slate-400 hover:text-slate-700 transition-colors">
                                    Tambah koreksi
                                </button>
                            </div>
                        </template>

                        <!-- Catatan -->
                        <template v-else>
                            <p class="text-xs text-slate-700 leading-relaxed">
                                <i class="pi pi-comment text-slate-300 mr-1 text-[10px]"></i>
                                {{ b.data.teks }}
                            </p>
                            <p class="text-[10px] text-slate-400 mt-1.5">
                                {{ tanggalJam(b.data.waktu) }} · {{ b.data.penulis_nama }}
                            </p>
                        </template>
                    </li>
                </ul>
            </div>

            <!-- ============ PANEL INPUT ============ -->
            <!-- Mobile: menempel di bawah (thumb zone). Desktop: kolom kanan sticky. -->
            <div class="fixed bottom-0 left-0 right-0 z-30 lg:static lg:z-auto
                        bg-white border-t lg:border border-slate-200 lg:rounded-[24px]
                        shadow-[0_-4px_24px_rgba(0,0,0,0.08)] lg:shadow-sm
                        p-4 lg:p-5 lg:sticky lg:top-4">
                <!-- Pilih mode -->
                <div class="flex bg-slate-50 p-1 rounded-xl mb-3">
                    <button type="button" v-for="m in MODE" :key="m.nilai" @click="gantiMode(m.nilai)"
                        :class="mode === m.nilai ? 'bg-white text-slate-800 shadow-sm font-bold' : 'text-slate-500'"
                        class="flex-1 px-3 py-2 text-xs rounded-lg transition-all">
                        {{ m.label }}
                    </button>
                </div>

                <!-- ---- MODE PENGUKURAN ---- -->
                <template v-if="mode === 'ukur'">
                    <div v-if="koreksiDari"
                        class="mb-2 px-3 py-2 bg-amber-50 border border-amber-200 rounded-xl flex justify-between items-center gap-2">
                        <p class="text-[11px] text-amber-900">
                            Mengoreksi <span class="font-bold">{{ koreksiDari.nama_label }}
                                {{ angka(koreksiDari.nilai, 2) }}{{ koreksiDari.satuan }}</span>
                        </p>
                        <button type="button" @click="batalKoreksi"
                            class="text-[11px] font-bold text-amber-700 shrink-0">Batal</button>
                    </div>

                    <!-- Ketukan 1: chip jenis, terakhir-dipakai di depan -->
                    <div class="flex gap-1.5 overflow-x-auto custom-scrollbar pb-2 -mx-1 px-1">
                        <button type="button" v-for="j in katalogTerurut" :key="j.id" @click="pilihJenis(j)"
                            :class="jenisDipilih?.id === j.id
                                ? 'bg-slate-900 text-white border-slate-900'
                                : 'bg-white text-slate-600 border-slate-200 hover:border-slate-400'"
                            class="shrink-0 px-3 py-2 rounded-xl border text-xs font-bold transition-colors whitespace-nowrap">
                            {{ j.nama }}
                            <span v-if="j.satuan" class="font-normal opacity-60">{{ j.satuan }}</span>
                        </button>
                    </div>

                    <template v-if="jenisDipilih">
                        <!-- Nilai -->
                        <div class="flex gap-2 mt-2">
                            <div class="relative flex-1">
                                <input v-if="jenisDipilih.tipe_nilai === 'ANGKA'" ref="kotakNilai"
                                    v-model="nilai" type="number" inputmode="decimal" step="any"
                                    :placeholder="jenisDipilih.nama"
                                    class="w-full text-2xl font-bold tabular-nums px-4 py-3 bg-slate-50 border border-slate-200
                                           rounded-2xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-900"
                                    @keyup.enter="simpanUkur" />
                                <input v-else ref="kotakNilai" v-model="nilaiTeks" type="text"
                                    :placeholder="jenisDipilih.nama"
                                    class="w-full text-base px-4 py-3 bg-slate-50 border border-slate-200 rounded-2xl
                                           text-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-900"
                                    @keyup.enter="simpanUkur" />
                                <span v-if="jenisDipilih.satuan"
                                    class="absolute right-4 top-1/2 -translate-y-1/2 text-sm font-bold text-slate-400">
                                    {{ jenisDipilih.satuan }}
                                </span>
                            </div>

                            <!-- Ketukan 2 -->
                            <button type="button" @click="simpanUkur" :disabled="!bisaSimpanUkur || sedangSimpan"
                                class="px-6 bg-slate-900 hover:bg-slate-800 disabled:opacity-40 text-white
                                       text-sm font-bold rounded-2xl transition-colors">
                                <i v-if="sedangSimpan" class="pi pi-spin pi-spinner"></i>
                                <span v-else>Simpan</span>
                            </button>
                        </div>

                        <p v-if="diLuarRentang" class="mt-1.5 text-[11px] text-amber-700 font-semibold">
                            Di luar rentang wajar ({{ angka(jenisDipilih.nilai_min, 0) }}–{{
                                angka(jenisDipilih.nilai_max, 0) }}{{ jenisDipilih.satuan }}).
                            Tetap bisa disimpan — angka nyata lebih berguna daripada angka yang rapi.
                        </p>

                        <!-- Tahap: proses vs hasil uji -->
                        <div class="flex gap-1.5 mt-2">
                            <button type="button" v-for="t in TAHAP" :key="t.nilai" @click="tahap = t.nilai"
                                :class="tahap === t.nilai ? 'bg-slate-100 text-slate-800 font-bold' : 'text-slate-400'"
                                class="px-3 py-1 rounded-lg text-[11px] transition-colors">
                                {{ t.label }}
                            </button>
                        </div>
                    </template>

                    <p v-else class="mt-3 text-xs text-slate-400 text-center py-2">
                        Pilih jenis pengukuran di atas.
                    </p>
                </template>

                <!-- ---- MODE CATATAN ---- -->
                <template v-else>
                    <textarea v-model="teksCatatan" rows="3" placeholder="Apa yang Anda lihat, cium, atau rasakan?"
                        class="w-full text-sm px-4 py-3 bg-slate-50 border border-slate-200 rounded-2xl text-slate-800
                               focus:outline-none focus:ring-2 focus:ring-slate-900"></textarea>
                    <button type="button" @click="simpanCatatanBaru" :disabled="!teksCatatan.trim() || sedangSimpan"
                        class="w-full mt-2 py-3 bg-slate-900 hover:bg-slate-800 disabled:opacity-40 text-white
                               text-sm font-bold rounded-2xl transition-colors">
                        <i v-if="sedangSimpan" class="pi pi-spin pi-spinner mr-1"></i>
                        Simpan Catatan
                    </button>
                </template>

                <!-- Aksi akhir sesi -->
                <div class="grid grid-cols-2 gap-2 mt-3 pt-3 border-t border-slate-100">
                    <button type="button" @click="dialogSelesai = true"
                        class="py-3 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-bold rounded-2xl transition-colors">
                        Selesaikan
                    </button>
                    <button type="button" @click="bukaDialogGagal"
                        class="py-3 bg-white border border-red-200 hover:bg-red-50 text-red-600 text-sm font-bold rounded-2xl transition-colors">
                        Gagalkan
                    </button>
                </div>
            </div>
        </div>

        <!-- ============ DIALOG SELESAIKAN ============ -->
        <div v-if="dialogSelesai" class="tirai" @click.self="dialogSelesai = false">
            <div class="kotak">
                <h3 class="text-base font-bold text-slate-800 mb-1">Selesaikan Sesi</h3>
                <p class="text-xs text-slate-500 mb-4">
                    Hasil akan dicatat dan sesi ditutup permanen.
                </p>

                <label class="block text-[11px] font-bold text-slate-600 mb-1">
                    Qty Hasil ({{ sesi?.satuan_kode }}) <span class="text-red-500">*</span>
                </label>
                <input v-model="qtyHasil" type="number" inputmode="decimal" step="0.001" min="0.001"
                    class="w-full text-xl font-bold tabular-nums px-4 py-3 bg-slate-50 border border-slate-200
                           rounded-2xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-900" />

                <p v-if="sesi?.jenis_sesi === 'PRODUKSI' && lebihDariTarget"
                    class="mt-2 text-[11px] text-red-600 font-semibold">
                    Hasil melebihi target {{ angka(sesi?.qty_target, 3) }}. Untuk sesi rutin backend akan
                    menolaknya — periksa timbangan atau resepnya.
                </p>

                <div v-if="sesi && !sesi.hasil_masuk_pool"
                    class="mt-3 px-3 py-2 bg-amber-50 border border-amber-200 rounded-xl">
                    <p class="text-[11px] text-amber-900 font-semibold">Hasil ini TIDAK masuk stok.</p>
                    <p class="text-[11px] text-amber-800 mt-0.5">
                        Angkanya tetap tercatat untuk perbandingan, tapi tidak akan muncul sebagai stok yang
                        bisa diklaim atau dijual.
                    </p>
                </div>

                <p v-if="galat" class="mt-3 text-[11px] text-red-600 whitespace-pre-line">{{ galat }}</p>

                <div class="flex justify-end gap-2 mt-5">
                    <button type="button" @click="dialogSelesai = false" class="tombol-batal">Batal</button>
                    <button type="button" @click="selesaikan"
                        :disabled="!qtyHasil || parseFloat(qtyHasil) <= 0 || sedangProses"
                        class="px-5 py-2 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-40 text-white
                               text-xs font-bold rounded-xl transition-colors">
                        Selesaikan
                    </button>
                </div>
            </div>
        </div>

        <!-- ============ DIALOG GAGALKAN ============ -->
        <!-- Satu-satunya titik di alur produksi yang menyentuh kepemilikan. -->
        <div v-if="dialogGagal" class="tirai" @click.self="dialogGagal = false">
            <div class="kotak">
                <h3 class="text-base font-bold text-red-700 mb-1">Gagalkan Sesi</h3>
                <p class="text-xs text-slate-500 mb-4">
                    Bahan sudah keluar dari pool dan tidak bisa dikembalikan. Nilainya akan dibebankan.
                </p>

                <div v-if="!pratinjauKerugian" class="py-6 text-center">
                    <i class="pi pi-spin pi-spinner text-slate-300 text-xl"></i>
                    <p class="text-xs text-slate-500 mt-2">Menghitung nilai kerugian...</p>
                </div>

                <template v-else>
                    <div class="bg-red-50 border border-red-200 rounded-2xl p-4 mb-4">
                        <p class="text-[10px] font-bold text-red-500 uppercase tracking-wider">Nilai yang hangus</p>
                        <p class="text-2xl font-black text-red-700 mt-0.5">
                            {{ rupiahPenuh(pratinjauKerugian.nilai_kerugian) }}
                        </p>
                        <p class="text-xs text-red-800 mt-2">
                            Dibebankan ke
                            <span class="font-bold">
                                {{ pratinjauKerugian.entitas_penanggung?.nama ?? 'entitas penanggung belum diisi' }}
                            </span>
                            <span v-if="pratinjauKerugian.entitas_penanggung">
                                ({{ pratinjauKerugian.entitas_penanggung.kode }})
                            </span>
                        </p>
                    </div>

                    <table class="w-full text-[11px] mb-4">
                        <thead class="text-slate-400">
                            <tr>
                                <th class="text-left font-semibold py-1">Bahan</th>
                                <th class="text-right font-semibold py-1">Qty</th>
                                <th class="text-right font-semibold py-1">Nilai</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="r in pratinjauKerugian.rincian" :key="r.bahan_kode"
                                class="border-t border-slate-100">
                                <td class="py-1.5 font-semibold text-slate-700">{{ r.bahan_kode }}</td>
                                <td class="py-1.5 text-right text-slate-600">
                                    {{ angka(r.qty, 3) }} {{ r.satuan_kode }}
                                </td>
                                <td class="py-1.5 text-right text-slate-800 font-semibold">
                                    {{ rupiahPenuh(r.nilai) }}
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </template>

                <label class="block text-[11px] font-bold text-slate-600 mb-1">Kategori Kegagalan</label>
                <select v-model="kategoriGagal" class="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-200
                               rounded-xl text-slate-700 mb-3 focus:outline-none focus:ring-2 focus:ring-slate-900">
                    <option v-for="k in KATEGORI_GAGAL" :key="k.nilai" :value="k.nilai">{{ k.label }}</option>
                </select>

                <label class="block text-[11px] font-bold text-slate-600 mb-1">
                    Alasan <span class="text-red-500">*</span>
                </label>
                <textarea v-model="alasanGagal" rows="3"
                    placeholder="Apa yang terjadi? Ini yang dibaca orang berikutnya sebelum mengulang percobaan."
                    class="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-700
                           focus:outline-none focus:ring-2 focus:ring-slate-900"></textarea>

                <p v-if="galat" class="mt-3 text-[11px] text-red-600 whitespace-pre-line">{{ galat }}</p>

                <div class="flex justify-end gap-2 mt-5">
                    <button type="button" @click="dialogGagal = false" class="tombol-batal">Batal</button>
                    <button type="button" @click="gagalkan"
                        :disabled="!alasanGagal.trim() || sedangProses"
                        class="px-5 py-2 bg-red-600 hover:bg-red-700 disabled:opacity-40 text-white
                               text-xs font-bold rounded-xl transition-colors">
                        Gagalkan &amp; Bebankan
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useSesiProduksi } from '../composables/useSesiProduksi'
import { usePengukuran, TAHAP } from '../composables/usePengukuran'
import { useToast } from '@/composables/useToast'
import { angka, tanggalJam } from '@/utils/format'

const props = defineProps({ id: { type: [String, Number], required: true } })

const MODE = [
    { nilai: 'ukur', label: 'Pengukuran' },
    { nilai: 'catatan', label: 'Catatan' },
]

const KATEGORI_GAGAL = [
    { nilai: 'PROSES', label: 'Kesalahan proses (suhu, waktu, pengaduk)' },
    { nilai: 'BAHAN', label: 'Bahan tidak sesuai' },
    { nilai: 'ALAT', label: 'Kerusakan alat' },
    { nilai: 'UJI', label: 'Tidak lulus uji' },
    { nilai: 'LAIN', label: 'Lain-lain' },
]

const router = useRouter()
const toast = useToast()

const {
    sesi, pratinjauKerugian, sedangProses, galat,
    muatDetail, jalankanAksi, muatPratinjauKerugian,
} = useSesiProduksi()

const {
    katalogTerurut, liniMasa, galat: galatUkur,
    muatKatalog, muatPengukuran, muatCatatan, simpanPengukuran, simpanCatatan,
} = usePengukuran()

// ---------- panel input ----------
const mode = ref('ukur')
const jenisDipilih = ref(null)
const nilai = ref('')
const nilaiTeks = ref('')
const tahap = ref('PROSES')
const teksCatatan = ref('')
const koreksiDari = ref(null)
const sedangSimpan = ref(false)
const kotakNilai = ref(null)

const gantiMode = (m) => { mode.value = m; galat.value = '' }

const pilihJenis = async (j) => {
    jenisDipilih.value = j
    nilai.value = ''
    nilaiTeks.value = ''
    await nextTick()
    kotakNilai.value?.focus()
}

const bisaSimpanUkur = computed(() => {
    if (!jenisDipilih.value) return false
    return jenisDipilih.value.tipe_nilai === 'ANGKA'
        ? nilai.value !== '' && !Number.isNaN(parseFloat(nilai.value))
        : nilaiTeks.value.trim() !== ''
})

const diLuarRentang = computed(() => {
    const j = jenisDipilih.value
    if (!j || j.tipe_nilai !== 'ANGKA' || nilai.value === '') return false
    if (j.nilai_min == null || j.nilai_max == null) return false
    const n = parseFloat(nilai.value)
    return n < parseFloat(j.nilai_min) || n > parseFloat(j.nilai_max)
})

const mulaiKoreksi = (p) => {
    mode.value = 'ukur'
    koreksiDari.value = p
    jenisDipilih.value = katalogTerurut.value.find((j) => j.id === p.nama) ?? null
    tahap.value = p.tahap
    nilai.value = ''
    nilaiTeks.value = ''
    window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' })
}

const batalKoreksi = () => { koreksiDari.value = null }

const simpanUkur = async () => {
    if (!bisaSimpanUkur.value) return
    sedangSimpan.value = true
    const hasil = await simpanPengukuran(props.id, {
        nama: jenisDipilih.value.id,
        tahap: tahap.value,
        nilai: jenisDipilih.value.tipe_nilai === 'ANGKA' ? nilai.value : null,
        nilai_teks: jenisDipilih.value.tipe_nilai === 'ANGKA' ? '' : nilaiTeks.value,
        mengoreksi: koreksiDari.value?.id ?? null,
        catatan: koreksiDari.value ? 'Koreksi entri sebelumnya.' : '',
    })
    sedangSimpan.value = false
    if (!hasil.success) { galat.value = hasil.message; return }

    // Nilai dikosongkan, JENIS TETAP dipilih — pengukuran berikutnya
    // biasanya jenis yang sama, jadi ketukan 1 tidak perlu diulang.
    nilai.value = ''
    nilaiTeks.value = ''
    koreksiDari.value = null
    toast.success('Tercatat.')
}

const simpanCatatanBaru = async () => {
    sedangSimpan.value = true
    const hasil = await simpanCatatan(props.id, { teks: teksCatatan.value.trim() })
    sedangSimpan.value = false
    if (!hasil.success) { galat.value = hasil.message; return }
    teksCatatan.value = ''
    toast.success('Catatan tersimpan.')
}

// ---------- timer ----------
const sekarang = ref(Date.now())
let jamTicker = null

const jamBerjalan = computed(() => {
    if (!sesi.value?.dimulai_pada) return '—'
    const selisih = Math.max(0, sekarang.value - new Date(sesi.value.dimulai_pada).getTime())
    const total = Math.floor(selisih / 1000)
    const j = String(Math.floor(total / 3600)).padStart(2, '0')
    const m = String(Math.floor((total % 3600) / 60)).padStart(2, '0')
    const d = String(total % 60).padStart(2, '0')
    return `${j}:${m}:${d}`
})

// ---------- aksi akhir ----------
const dialogSelesai = ref(false)
const dialogGagal = ref(false)
const qtyHasil = ref('')
const alasanGagal = ref('')
const kategoriGagal = ref('PROSES')

const lebihDariTarget = computed(() =>
    !!sesi.value && !!qtyHasil.value
    && parseFloat(qtyHasil.value) > parseFloat(sesi.value.qty_target))

const rupiahPenuh = (n) => `Rp ${Number(n || 0).toLocaleString('id-ID', { maximumFractionDigits: 0 })}`

const bukaDialogGagal = () => {
    dialogGagal.value = true
    galat.value = ''
    muatPratinjauKerugian(props.id)
}

const selesaikan = async () => {
    const hasil = await jalankanAksi(props.id, 'selesaikan', { qty_hasil: qtyHasil.value })
    if (!hasil.success) return
    dialogSelesai.value = false
    toast.success('Sesi selesai.')
    router.push({ name: 'produksi-sesi-detail', params: { id: props.id } })
}

const gagalkan = async () => {
    const hasil = await jalankanAksi(props.id, 'gagalkan', {
        alasan: alasanGagal.value.trim(),
        kategori_kegagalan: kategoriGagal.value,
    })
    if (!hasil.success) return
    dialogGagal.value = false
    toast.warn('Sesi ditandai gagal, kerugian dibebankan.')
    router.push({ name: 'produksi-sesi-detail', params: { id: props.id } })
}

onMounted(async () => {
    await Promise.all([
        muatDetail(props.id),
        muatKatalog(),
        muatPengukuran(props.id),
        muatCatatan(props.id),
    ])
    if (galatUkur.value && !galat.value) galat.value = galatUkur.value
    jamTicker = setInterval(() => { sekarang.value = Date.now() }, 1000)
})

onUnmounted(() => clearInterval(jamTicker))
</script>

<style scoped>
.animate-fade-in {
    animation: fadeIn 0.3s ease-out forwards;
}

@keyframes fadeIn {
    from {
        opacity: 0;
    }

    to {
        opacity: 1;
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

.tirai {
    position: fixed;
    inset: 0;
    z-index: 50;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1rem;
    background: rgba(15, 23, 42, .45);
}

.kotak {
    width: 100%;
    max-width: 26rem;
    max-height: 90vh;
    overflow-y: auto;
    background: #fff;
    border-radius: 24px;
    padding: 1.5rem;
    box-shadow: 0 20px 50px rgba(0, 0, 0, .2);
}

.tombol-batal {
    padding: .5rem 1rem;
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: .75rem;
    font-size: .75rem;
    font-weight: 700;
    color: #334155;
    cursor: pointer;
}

.tombol-batal:hover {
    background: #f8fafc;
}
</style>
