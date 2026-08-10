<!--
  features/produksi/views/SesiDetail.vue
  =======================================
  Arsip satu sesi: bahan (rencana vs aktual), hasil, dan lini masa
  pengukuran + catatan digabung urut waktu.

  Tombol aksi mengikuti status — `batalkan` HANYA muncul di DRAFT. Backend
  menolaknya di status lain (§D), jadi menampilkannya lalu ditolak cuma
  mengajari operator bahwa tombol di layar ini tidak bisa dipercaya.
-->
<template>
    <div class="flex flex-col w-full animate-fade-in">
        <div class="mb-4 md:mb-6 flex justify-between items-end gap-3 flex-wrap">
            <div class="min-w-0">
                <p class="text-xs text-slate-400 mb-1">
                    <router-link :to="{ name: 'produksi-sesi-list' }" class="hover:text-slate-700 transition-colors">
                        Sesi Produksi</router-link> › Detail
                </p>
                <h2 class="text-xl md:text-2xl font-bold text-slate-800 tracking-tight">
                    {{ sesi?.nomor ?? 'Memuat...' }}
                </h2>
                <div v-if="sesi" class="flex items-center gap-2 mt-2 flex-wrap">
                    <span :class="kelasStatus(sesi.status)"
                        class="px-2.5 py-1 rounded-full text-[10px] font-bold uppercase">{{ sesi.status }}</span>
                    <span :class="sesi.jenis_sesi === 'RND'
                        ? 'bg-violet-50 text-violet-700 border-violet-200'
                        : 'bg-slate-100 text-slate-600 border-slate-200'"
                        class="px-2 py-1 rounded-lg text-[10px] font-bold border">
                        {{ sesi.jenis_sesi === 'RND' ? 'R&D' : 'RUTIN' }}
                    </span>
                    <span class="text-xs text-slate-500">{{ tanggal(sesi.tanggal) }} · {{ sesi.grup_bahan_kode }}</span>
                </div>
            </div>

            <div v-if="sesi" class="flex items-center gap-2">
                <router-link v-if="sesi.status === 'BERJALAN'"
                    :to="{ name: 'produksi-sesi-berjalan', params: { id: sesi.id } }"
                    class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-xl transition-colors">
                    <i class="pi pi-play mr-1"></i> Buka Layar Kerja
                </router-link>

                <template v-if="sesi.status === 'DRAFT'">
                    <button type="button" @click="bukaDialogMulai"
                        class="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold rounded-xl transition-colors">
                        Mulai Sesi
                    </button>
                    <!-- batalkan/ HANYA di DRAFT -->
                    <button type="button" @click="dialogBatal = true"
                        class="px-4 py-2 bg-white border border-slate-200 hover:bg-slate-50 text-slate-600 text-xs font-bold rounded-xl transition-colors">
                        Batalkan
                    </button>
                </template>
            </div>
        </div>

        <p v-if="galat" class="mb-4 px-4 py-3 bg-red-50 text-red-600 rounded-xl text-xs whitespace-pre-line">
            {{ galat }}
        </p>

        <!-- Penanda hasil non-stok -->
        <div v-if="sesi && !sesi.hasil_masuk_pool"
            class="mb-4 flex items-start gap-3 px-4 py-3 bg-amber-50 border border-amber-200 rounded-2xl">
            <i class="pi pi-exclamation-triangle text-amber-600 mt-0.5"></i>
            <div>
                <p class="text-xs font-bold text-amber-900">Hasil sesi ini TIDAK masuk stok</p>
                <p class="text-xs text-amber-800 mt-0.5 leading-relaxed">
                    Angkanya tercatat untuk perbandingan antar batch, tapi barangnya tidak pernah menjadi
                    stok pool — tidak bisa diklaim entitas dan tidak boleh dijual.
                </p>
            </div>
        </div>

        <div v-if="sesi" class="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <!-- Ringkasan angka -->
            <div class="lg:col-span-3 grid grid-cols-2 md:grid-cols-4 gap-4">
                <div class="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm">
                    <p class="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Target</p>
                    <h3 class="text-lg font-black text-slate-800">
                        {{ angka(sesi.qty_target, 3) }}
                        <span class="text-xs font-bold text-slate-400">{{ sesi.satuan_kode }}</span>
                    </h3>
                </div>
                <div class="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm">
                    <p class="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Hasil</p>
                    <h3 class="text-lg font-black text-slate-800">
                        {{ angka(sesi.qty_hasil, 3) }}
                        <span class="text-xs font-bold text-slate-400">{{ sesi.satuan_kode }}</span>
                    </h3>
                </div>
                <div class="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm">
                    <p class="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Susut</p>
                    <h3 class="text-lg font-black" :class="parseFloat(sesi.susut) > 0 ? 'text-amber-600' : 'text-slate-800'">
                        {{ angka(sesi.susut, 3) }}
                    </h3>
                </div>
                <div class="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm">
                    <p class="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Rendemen</p>
                    <h3 class="text-lg font-black text-slate-800">
                        {{ (parseFloat(sesi.rendemen || 0) * 100).toFixed(1) }}%
                    </h3>
                </div>
            </div>

            <!-- Bahan -->
            <div class="lg:col-span-1 bg-white border border-slate-200 rounded-[24px] p-4 md:p-5 shadow-sm">
                <h3 class="text-sm font-bold text-slate-800 mb-1">Bahan Terpakai</h3>
                <p class="text-xs text-slate-500 mb-4">Rencana dibanding yang benar-benar ditimbang</p>

                <div v-for="i in sesi.input" :key="i.id" class="py-2 border-b border-slate-100 last:border-0">
                    <div class="flex justify-between items-start gap-2">
                        <div class="min-w-0">
                            <p class="text-xs font-bold text-slate-800">{{ i.bahan_kode }}</p>
                            <p class="text-[11px] text-slate-500 truncate">{{ i.bahan_nama }}</p>
                        </div>
                        <div class="text-right shrink-0">
                            <p class="text-xs font-bold text-slate-800 tabular-nums">
                                {{ angka(i.qty_aktual, 3) }} {{ i.satuan_kode }}
                            </p>
                            <p class="text-[10px] text-slate-400 tabular-nums">
                                rencana {{ angka(i.qty_rencana, 3) }}
                            </p>
                        </div>
                    </div>
                    <p v-if="parseFloat(i.selisih) !== 0" class="text-[10px] font-bold mt-0.5"
                        :class="parseFloat(i.selisih) > 0 ? 'text-amber-600' : 'text-blue-600'">
                        selisih {{ parseFloat(i.selisih) > 0 ? '+' : '' }}{{ angka(i.selisih, 3) }}
                    </p>
                </div>

                <div v-if="sesi.jenis_sesi === 'RND'" class="mt-4 pt-4 border-t border-slate-100">
                    <p class="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Entitas Penanggung</p>
                    <p class="text-xs font-bold text-slate-800">
                        {{ sesi.entitas_penanggung_nama ?? '—' }}
                        <span v-if="sesi.entitas_penanggung_kode" class="text-slate-400 font-normal">
                            ({{ sesi.entitas_penanggung_kode }})
                        </span>
                    </p>
                    <p v-if="sesi.status === 'GAGAL' && sesi.nilai_kerugian"
                        class="text-xs text-red-600 font-bold mt-1">
                        Dibebankan {{ rupiahPenuh(sesi.nilai_kerugian) }}
                    </p>
                </div>

                <div v-if="sesi.catatan" class="mt-4 pt-4 border-t border-slate-100">
                    <p class="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Catatan Sesi</p>
                    <p class="text-xs text-slate-600 whitespace-pre-line leading-relaxed">{{ sesi.catatan }}</p>
                </div>
            </div>

            <!-- Lini masa -->
            <div class="lg:col-span-2 bg-white border border-slate-200 rounded-[24px] p-4 md:p-5 shadow-sm">
                <div class="flex justify-between items-center mb-4">
                    <div>
                        <h3 class="text-sm font-bold text-slate-800">Lini Masa Eksperimen</h3>
                        <p class="text-xs text-slate-500">Pengukuran dan catatan, urut waktu</p>
                    </div>
                    <p class="text-xs text-slate-400">{{ liniMasa.length }} entri</p>
                </div>

                <p v-if="liniMasa.length === 0" class="py-10 text-center text-xs text-slate-400">
                    Tidak ada pengukuran maupun catatan untuk sesi ini.
                </p>

                <ol class="relative border-l border-slate-200 ml-2">
                    <li v-for="b in liniMasaKronologis" :key="b.kunci" class="ml-4 pb-4 last:pb-0"
                        :class="b.digantikan ? 'opacity-50' : ''">
                        <span class="absolute -left-[5px] w-2.5 h-2.5 rounded-full"
                            :class="b.jenis === 'ukur' ? 'bg-slate-400' : 'bg-slate-200'"></span>

                        <template v-if="b.jenis === 'ukur'">
                            <div class="flex justify-between items-start gap-2">
                                <p class="text-xs font-bold text-slate-800">
                                    {{ b.data.nama_label }}
                                    <span v-if="b.data.tahap === 'UJI'"
                                        class="ml-1 px-1.5 py-0.5 rounded bg-sky-50 text-sky-700 text-[9px] font-bold border border-sky-200">UJI</span>
                                    <span v-if="b.data.mengoreksi"
                                        class="ml-1 px-1.5 py-0.5 rounded bg-amber-50 text-amber-700 text-[9px] font-bold border border-amber-200">KOREKSI</span>
                                </p>
                                <p class="text-sm font-black text-slate-800 shrink-0 tabular-nums">
                                    {{ b.data.nilai !== null ? angka(b.data.nilai, 2) : b.data.nilai_teks }}
                                    <span class="text-[10px] font-bold text-slate-400">{{ b.data.satuan }}</span>
                                </p>
                            </div>
                            <p v-if="b.data.catatan" class="text-[11px] text-slate-500 mt-0.5">{{ b.data.catatan }}</p>
                            <p class="text-[10px] text-slate-400 mt-0.5">
                                {{ tanggalJam(b.data.waktu) }} · {{ b.data.dicatat_oleh_nama }}
                                <span v-if="b.digantikan" class="font-bold text-amber-600">· sudah dikoreksi</span>
                            </p>
                        </template>

                        <template v-else>
                            <p class="text-xs text-slate-700 leading-relaxed">
                                <i class="pi pi-comment text-slate-300 mr-1 text-[10px]"></i>{{ b.data.teks }}
                            </p>
                            <p class="text-[10px] text-slate-400 mt-0.5">
                                {{ tanggalJam(b.data.waktu) }} · {{ b.data.penulis_nama }}
                            </p>
                        </template>
                    </li>
                </ol>
            </div>
        </div>

        <!-- ============ DIALOG MULAI ============ -->
        <!-- Titik tidak bisa mundur: setelah ini bahan benar-benar keluar dari pool. -->
        <div v-if="dialogMulai" class="tirai" @click.self="dialogMulai = false">
            <div class="kotak">
                <h3 class="text-base font-bold text-slate-800 mb-1">Mulai Sesi</h3>
                <p class="text-xs text-slate-500 mb-4">
                    Sesuaikan angka ke hasil timbangan sebenarnya. Yang dicatat harus angka nyata,
                    bukan angka rencana.
                </p>

                <div v-for="b in barisMulai" :key="b.bahan_id" class="mb-3">
                    <label class="block text-[11px] font-bold text-slate-600 mb-1">
                        {{ b.bahan_kode }} <span class="font-normal text-slate-400">— {{ b.bahan_nama }}</span>
                    </label>
                    <div class="flex items-center gap-2">
                        <input v-model="b.qty_aktual" type="number" inputmode="decimal" step="0.001"
                            class="flex-1 text-sm font-bold tabular-nums px-3 py-2 bg-slate-50 border border-slate-200
                                   rounded-xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-900" />
                        <span class="text-xs font-bold text-slate-400 w-10">{{ b.satuan_kode }}</span>
                    </div>
                </div>

                <div class="mt-4 px-4 py-3 bg-red-50 border border-red-200 rounded-2xl">
                    <p class="text-xs font-bold text-red-900 mb-1">
                        <i class="pi pi-exclamation-triangle mr-1"></i> Titik tidak bisa mundur
                    </p>
                    <ul class="text-xs text-red-800 leading-relaxed list-disc ml-4">
                        <li v-for="b in barisMulai" :key="b.bahan_id">
                            <span class="font-bold">{{ angka(b.qty_aktual, 3) }} {{ b.satuan_kode }}</span>
                            {{ b.bahan_kode }} akan keluar dari pool
                        </li>
                    </ul>
                    <p class="text-xs text-red-800 mt-2 font-semibold">
                        Sesi tidak bisa dibatalkan setelah ini. Kalau percobaan gagal, jalurnya adalah
                        "Gagalkan" — dan nilai bahan di atas akan dibebankan ke entitas penanggung.
                    </p>
                </div>

                <p v-if="galat" class="mt-3 text-[11px] text-red-600 whitespace-pre-line">{{ galat }}</p>

                <div class="flex justify-end gap-2 mt-5">
                    <button type="button" @click="dialogMulai = false" class="tombol-batal">Batal</button>
                    <button type="button" @click="mulai" :disabled="sedangProses"
                        class="px-5 py-2 bg-slate-900 hover:bg-slate-800 disabled:opacity-40 text-white
                               text-xs font-bold rounded-xl transition-colors">
                        Ya, keluarkan bahan
                    </button>
                </div>
            </div>
        </div>

        <!-- ============ DIALOG BATALKAN ============ -->
        <div v-if="dialogBatal" class="tirai" @click.self="dialogBatal = false">
            <div class="kotak">
                <h3 class="text-base font-bold text-slate-800 mb-1">Batalkan Sesi</h3>
                <p class="text-xs text-slate-500 mb-4">
                    Sesi ini masih draft — belum ada bahan yang keluar dari pool, jadi tidak ada nilai
                    yang perlu dibebankan.
                </p>

                <label class="block text-[11px] font-bold text-slate-600 mb-1">
                    Alasan <span class="text-red-500">*</span>
                </label>
                <textarea v-model="alasanBatal" rows="3"
                    class="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-700
                           focus:outline-none focus:ring-2 focus:ring-slate-900"></textarea>

                <p v-if="galat" class="mt-3 text-[11px] text-red-600 whitespace-pre-line">{{ galat }}</p>

                <div class="flex justify-end gap-2 mt-5">
                    <button type="button" @click="dialogBatal = false" class="tombol-batal">Kembali</button>
                    <button type="button" @click="batalkan" :disabled="!alasanBatal.trim() || sedangProses"
                        class="px-5 py-2 bg-slate-900 hover:bg-slate-800 disabled:opacity-40 text-white
                               text-xs font-bold rounded-xl transition-colors">
                        Batalkan Sesi
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useSesiProduksi } from '../composables/useSesiProduksi'
import { usePengukuran } from '../composables/usePengukuran'
import { useToast } from '@/composables/useToast'
import { angka, tanggal, tanggalJam } from '@/utils/format'

const props = defineProps({ id: { type: [String, Number], required: true } })

const toast = useToast()
const { sesi, sedangProses, galat, muatDetail, jalankanAksi } = useSesiProduksi()
const { liniMasa, muatPengukuran, muatCatatan } = usePengukuran()

/** Detail dibaca sebagai arsip: paling lama di atas, seperti membaca jurnal. */
const liniMasaKronologis = computed(() => [...liniMasa.value].reverse())

const dialogMulai = ref(false)
const dialogBatal = ref(false)
const alasanBatal = ref('')
const barisMulai = ref([])

const rupiahPenuh = (n) => `Rp ${Number(n || 0).toLocaleString('id-ID', { maximumFractionDigits: 0 })}`

const bukaDialogMulai = () => {
    galat.value = ''
    barisMulai.value = (sesi.value?.input ?? []).map((i) => ({
        bahan_id: i.bahan,
        bahan_kode: i.bahan_kode,
        bahan_nama: i.bahan_nama,
        satuan_kode: i.satuan_kode,
        qty_aktual: i.qty_aktual,
        tangki_id: i.tangki ?? null,
    }))
    dialogMulai.value = true
}

const mulai = async () => {
    const hasil = await jalankanAksi(props.id, 'mulai', {
        baris: barisMulai.value.map((b) => ({
            bahan_id: b.bahan_id,
            qty_aktual: b.qty_aktual,
            tangki_id: b.tangki_id,
        })),
    })
    if (!hasil.success) return
    dialogMulai.value = false
    toast.success('Sesi berjalan. Bahan sudah keluar dari pool.')
}

const batalkan = async () => {
    const hasil = await jalankanAksi(props.id, 'batalkan', { alasan: alasanBatal.value.trim() })
    if (!hasil.success) return
    dialogBatal.value = false
    toast.info('Sesi dibatalkan.')
}

const kelasStatus = (st) => ({
    DRAFT: 'bg-slate-100 text-slate-600',
    BERJALAN: 'bg-blue-50 text-blue-600',
    SELESAI: 'bg-emerald-50 text-emerald-600',
    GAGAL: 'bg-red-50 text-red-600',
    BATAL: 'bg-slate-100 text-slate-500',
}[st] ?? 'bg-slate-100 text-slate-600')

onMounted(() => {
    muatDetail(props.id)
    muatPengukuran(props.id)
    muatCatatan(props.id)
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
