<!--
  features/produksi/views/SesiForm.vue
  =====================================
  Buat sesi. Form BERCABANG pada jenis_sesi — dua alur yang berbeda cukup
  jauh untuk tidak dipaksa jadi satu set field.

  PRODUKSI  resep wajib ada (dipilih di sini, versinya ditetapkan server
            lewat Resep.berlaku()). entitas_penanggung disembunyikan —
            produksi rutin tidak membakar nilai siapa pun.
  RND       resep memang belum ada — itu yang sedang dicari. produk_jadi
            dan entitas_penanggung wajib, bahan diketik manual.

  §D: POST produksi/sesi/      body { grup_bahan_id, produk_jadi_id, ... }
      POST produksi/sesi/rnd/  body { ..., entitas_penanggung_id, baris[] }
-->
<template>
    <div class="flex flex-col w-full animate-fade-in max-w-4xl">
        <div class="mb-4 md:mb-6">
            <p class="text-xs text-slate-400 mb-1">
                <router-link :to="{ name: 'produksi-sesi-list' }" class="hover:text-slate-700 transition-colors">
                    Sesi Produksi</router-link> › Buat
            </p>
            <h2 class="text-xl md:text-2xl font-bold text-slate-800 tracking-tight">Sesi Baru</h2>
        </div>

        <!-- Pemilih jenis -->
        <div class="bg-white border border-slate-200 rounded-[24px] p-4 md:p-6 shadow-sm mb-4">
            <p class="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-3">Jenis Sesi</p>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <button type="button" @click="gantiJenis('PRODUKSI')"
                    :class="jenis === 'PRODUKSI' ? 'border-slate-900 bg-slate-50' : 'border-slate-200 hover:border-slate-300'"
                    class="text-left border-2 rounded-2xl p-4 transition-colors">
                    <p class="text-sm font-bold text-slate-800">Produksi Rutin</p>
                    <p class="text-xs text-slate-500 mt-1">Resep sudah ada, hasil masuk stok.</p>
                </button>
                <button type="button" @click="gantiJenis('RND')"
                    :class="jenis === 'RND' ? 'border-violet-500 bg-violet-50' : 'border-slate-200 hover:border-slate-300'"
                    class="text-left border-2 rounded-2xl p-4 transition-colors">
                    <p class="text-sm font-bold text-slate-800">R&amp;D / Percobaan</p>
                    <p class="text-xs text-slate-500 mt-1">Resep belum ada — justru itu yang dicari.</p>
                </button>
            </div>
        </div>

        <form class="bg-white border border-slate-200 rounded-[24px] p-4 md:p-6 shadow-sm" @submit.prevent="simpan">
            <p v-if="galat" class="mb-4 px-4 py-3 bg-red-50 text-red-600 rounded-xl text-xs whitespace-pre-line">
                {{ galat }}
            </p>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <!-- Grup bahan -->
                <div>
                    <label class="blok-label">Grup Bahan <span class="text-red-500">*</span></label>
                    <select v-model="form.grup_bahan_id" class="blok-input">
                        <option :value="null" disabled>Pilih grup bahan</option>
                        <option v-for="g in daftarGrupBahan" :key="g.id" :value="g.id">
                            {{ g.kode }} — {{ g.nama }}
                        </option>
                    </select>
                    <p v-if="galatField.grup_bahan_id" class="blok-galat">{{ galatField.grup_bahan_id }}</p>
                    <p class="blok-bantu">Satu sesi tidak boleh melintasi grup — pool PT dan BERSAMA tidak pernah
                        bercampur.</p>
                </div>

                <!-- Tanggal -->
                <div>
                    <label class="blok-label">Tanggal <span class="text-red-500">*</span></label>
                    <input type="date" v-model="form.tanggal" class="blok-input" />
                    <p v-if="galatField.tanggal" class="blok-galat">{{ galatField.tanggal }}</p>
                </div>

                <!-- PRODUKSI: pilih resep -->
                <div v-if="jenis === 'PRODUKSI'" class="md:col-span-2">
                    <label class="blok-label">Resep <span class="text-red-500">*</span></label>
                    <select v-model="resepId" class="blok-input">
                        <option :value="null" disabled>Pilih resep aktif</option>
                        <option v-for="r in daftarResep" :key="r.id" :value="r.id">
                            {{ r.produk_jadi_kode }} v{{ r.versi }} — {{ r.nama || r.produk_jadi_nama }}
                        </option>
                    </select>
                    <p v-if="galatField.produk_jadi_id" class="blok-galat">{{ galatField.produk_jadi_id }}</p>
                    <p class="blok-bantu">
                        Versi resep yang dipakai ditetapkan server dari tanggal sesi, bukan dari pilihan ini.
                    </p>
                </div>

                <!-- RND: produk jadi + penanggung -->
                <template v-if="jenis === 'RND'">
                    <div>
                        <label class="blok-label">Produk yang Dituju <span class="text-red-500">*</span></label>
                        <select v-model="form.produk_jadi_id" class="blok-input">
                            <option :value="null" disabled>Pilih produk</option>
                            <option v-for="p in daftarProduk" :key="p.id" :value="p.id">
                                {{ p.kode }} — {{ p.nama }}
                            </option>
                        </select>
                        <p v-if="galatField.produk_jadi_id" class="blok-galat">{{ galatField.produk_jadi_id }}</p>
                    </div>

                    <div>
                        <label class="blok-label">Entitas Penanggung <span class="text-red-500">*</span></label>
                        <select v-model="form.entitas_penanggung_id" class="blok-input">
                            <option :value="null" disabled>Pilih entitas</option>
                            <option v-for="e in daftarEntitas" :key="e.id" :value="e.id">
                                {{ e.kode }} — {{ e.nama }}
                            </option>
                        </select>
                        <p v-if="galatField.entitas_penanggung_id" class="blok-galat">
                            {{ galatField.entitas_penanggung_id }}
                        </p>
                    </div>

                    <div class="md:col-span-2 bg-violet-50 border border-violet-200 rounded-2xl p-4">
                        <p class="text-xs font-bold text-violet-900 mb-1">
                            <i class="pi pi-info-circle mr-1"></i> Kenapa entitas penanggung diperlukan?
                        </p>
                        <p class="text-xs text-violet-800 leading-relaxed">
                            Bahan percobaan diambil dari pool yang ada pemiliknya. Kalau eksperimen gagal,
                            nilai bahan itu hangus dan harus ada yang menanggungnya — kalau tidak, catatan
                            siapa berhutang ke siapa dalam grup ini jadi tidak akurat.
                            Entitas yang Anda pilih di sini yang akan dibebani nilainya.
                        </p>
                    </div>
                </template>

                <!-- Target -->
                <div>
                    <label class="blok-label">Qty Target <span class="text-red-500">*</span></label>
                    <input type="number" step="0.001" min="0.001" v-model="form.qty_target" class="blok-input"
                        placeholder="0.000" />
                    <p v-if="galatField.qty_target" class="blok-galat">{{ galatField.qty_target }}</p>
                </div>

                <!-- RND: hasil masuk pool -->
                <div v-if="jenis === 'RND'" class="flex items-start gap-3 pt-6">
                    <input id="masukPool" type="checkbox" v-model="form.hasil_masuk_pool"
                        class="mt-0.5 w-4 h-4 rounded border-slate-300" />
                    <label for="masukPool" class="text-xs text-slate-600 leading-relaxed cursor-pointer">
                        <span class="font-bold text-slate-800 block">Hasil masuk stok pool</span>
                        Biarkan mati untuk trial uji lab. Hasil yang masuk pool bisa diklaim dan dijual —
                        batch yang belum lulus uji sebaiknya tidak.
                    </label>
                </div>
            </div>

            <!-- RND: bahan manual -->
            <div v-if="jenis === 'RND'" class="mt-6 pt-6 border-t border-slate-100">
                <div class="flex justify-between items-center mb-3">
                    <div>
                        <p class="text-sm font-bold text-slate-800">Bahan Percobaan</p>
                        <p class="text-xs text-slate-500">Tidak ada resep untuk mengisinya otomatis.</p>
                    </div>
                    <button type="button" @click="tambahBaris"
                        class="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold rounded-lg transition-colors">
                        <i class="pi pi-plus mr-1"></i> Baris
                    </button>
                </div>

                <p v-if="galatField.baris" class="blok-galat mb-2">{{ galatField.baris }}</p>

                <div v-for="(b, i) in form.baris" :key="i" class="flex gap-2 mb-2">
                    <select v-model="b.bahan_id" class="blok-input flex-1">
                        <option :value="null" disabled>Pilih bahan</option>
                        <option v-for="p in daftarProduk" :key="p.id" :value="p.id">{{ p.kode }} — {{ p.nama }}</option>
                    </select>
                    <input type="number" step="0.001" min="0.001" v-model="b.qty_rencana"
                        class="blok-input w-32" placeholder="Qty" />
                    <button type="button" @click="form.baris.splice(i, 1)"
                        class="px-3 text-slate-400 hover:text-red-500 transition-colors" aria-label="Hapus baris">
                        <i class="pi pi-times"></i>
                    </button>
                </div>

                <p v-if="form.baris.length === 0" class="text-xs text-slate-400 py-3">Belum ada bahan.</p>
            </div>

            <!-- Kapasitas -->
            <div v-if="kapasitas" class="mt-6 bg-slate-50 border border-slate-200 rounded-2xl p-4">
                <div class="flex justify-between items-start gap-3 flex-wrap mb-3">
                    <div>
                        <p class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Kapasitas dari isi pool
                        </p>
                        <p class="text-sm font-bold text-slate-800 mt-0.5">
                            Maksimum {{ angka(kapasitas.maksimum, 3) }} unit
                        </p>
                    </div>
                    <p class="text-xs text-slate-600">
                        Resep <span class="font-semibold">{{ kapasitas.resep }}</span> ·
                        dibatasi
                        <span class="font-bold text-amber-700">{{ (kapasitas.pembatas || []).join(', ') }}</span>
                    </p>
                </div>

                <table class="w-full text-xs">
                    <thead class="text-slate-400">
                        <tr>
                            <th class="text-left font-semibold py-1">Bahan</th>
                            <th class="text-right font-semibold py-1">Tersedia</th>
                            <th class="text-right font-semibold py-1">Per unit</th>
                            <th class="text-right font-semibold py-1">Cukup untuk</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="r in kapasitas.rincian" :key="r.bahan_id" class="border-t border-slate-200">
                            <td class="py-1.5 font-semibold text-slate-700">{{ r.bahan }}</td>
                            <td class="py-1.5 text-right text-slate-600">{{ angka(r.tersedia, 3) }}</td>
                            <td class="py-1.5 text-right text-slate-600">{{ angka(r.per_unit, 4) }}</td>
                            <td class="py-1.5 text-right font-bold"
                                :class="melebihiTarget(r) ? 'text-slate-800' : 'text-red-600'">
                                {{ angka(r.cukup_untuk, 3) }}
                            </td>
                        </tr>
                    </tbody>
                </table>

                <p v-if="targetMelebihiKapasitas" class="mt-3 text-xs text-red-600 font-semibold">
                    Target {{ angka(form.qty_target, 3) }} melebihi kapasitas
                    {{ angka(kapasitas.maksimum, 3) }}. Backend akan menolak sesi ini.
                </p>
            </div>

            <!-- Catatan -->
            <div class="mt-6">
                <label class="blok-label">Catatan</label>
                <textarea v-model="form.catatan" rows="2" class="blok-input"
                    placeholder="Opsional — konteks percobaan, kondisi bahan, dsb."></textarea>
            </div>

            <div class="mt-6 pt-6 border-t border-slate-100 flex justify-end gap-2">
                <router-link :to="{ name: 'produksi-sesi-list' }"
                    class="px-4 py-2 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-bold rounded-xl transition-colors">
                    Batal
                </router-link>
                <button type="submit" :disabled="sedangProses"
                    class="px-5 py-2 bg-slate-900 hover:bg-slate-800 disabled:opacity-50 text-white text-xs font-bold rounded-xl transition-colors">
                    <i v-if="sedangProses" class="pi pi-spin pi-spinner mr-1"></i>
                    Simpan sebagai Draft
                </button>
            </div>

            <p class="mt-3 text-xs text-slate-400 text-right">
                Menyimpan belum menyentuh stok. Bahan baru keluar dari pool saat sesi dimulai.
            </p>
        </form>
    </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useSesiProduksi } from '../composables/useSesiProduksi'
import { useToast } from '@/composables/useToast'
import { angka, hariIni } from '@/utils/format'

const router = useRouter()
const toast = useToast()
const {
    daftarResep, kapasitas, daftarGrupBahan, daftarEntitas, daftarProduk,
    sedangProses, galat, galatField,
    muatResep, muatKapasitas, muatAcuan, buatSesi,
} = useSesiProduksi()

const jenis = ref('PRODUKSI')
const resepId = ref(null)

const form = reactive({
    grup_bahan_id: null,
    produk_jadi_id: null,
    entitas_penanggung_id: null,
    qty_target: '',
    tanggal: hariIni(),
    hasil_masuk_pool: false,
    catatan: '',
    baris: [],
})

const gantiJenis = (j) => {
    jenis.value = j
    // Membersihkan field yang tidak berlaku di cabang lain, supaya tidak
    // ada nilai siluman yang ikut terkirim.
    form.entitas_penanggung_id = null
    form.produk_jadi_id = null
    form.baris = []
    resepId.value = null
    form.hasil_masuk_pool = j === 'PRODUKSI'
    kapasitas.value = null
}

/** Resep menentukan produk_jadi — yang dikirim ke §D adalah produk_jadi_id. */
watch(resepId, (id) => {
    const r = daftarResep.value.find((x) => x.id === id)
    form.produk_jadi_id = r?.produk_jadi ?? null
})

// Kapasitas hanya berlaku untuk alur ber-resep. RND tanpa resep tidak punya
// dasar hitung — hitung_kapasitas() memang butuh Resep.berlaku().
watch(
    () => [form.grup_bahan_id, form.produk_jadi_id, form.tanggal, jenis.value],
    () => {
        if (jenis.value !== 'PRODUKSI') { kapasitas.value = null; return }
        muatKapasitas({ grup: form.grup_bahan_id, produk: form.produk_jadi_id, tanggal: form.tanggal })
    },
)

const melebihiTarget = (r) =>
    !form.qty_target || parseFloat(r.cukup_untuk) >= parseFloat(form.qty_target)

const targetMelebihiKapasitas = computed(() =>
    !!kapasitas.value && !!form.qty_target
    && parseFloat(form.qty_target) > parseFloat(kapasitas.value.maksimum))

const tambahBaris = () => form.baris.push({ bahan_id: null, qty_rencana: '' })

const simpan = async () => {
    const dasar = {
        grup_bahan_id: form.grup_bahan_id,
        produk_jadi_id: form.produk_jadi_id,
        qty_target: form.qty_target,
        tanggal: form.tanggal,
        catatan: form.catatan,
    }
    const payload = jenis.value === 'RND'
        ? {
            ...dasar,
            entitas_penanggung_id: form.entitas_penanggung_id,
            hasil_masuk_pool: form.hasil_masuk_pool,
            baris: form.baris,
        }
        : dasar

    const hasil = await buatSesi(jenis.value, payload)
    if (!hasil.success) return

    toast.success(`Sesi ${hasil.data.nomor} dibuat sebagai draft.`)
    router.push({ name: 'produksi-sesi-detail', params: { id: hasil.data.id } })
}

onMounted(() => {
    muatAcuan()
    muatResep()
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

.blok-label {
    display: block;
    font-size: .6875rem;
    font-weight: 700;
    color: #475569;
    margin-bottom: .35rem;
}

.blok-input {
    width: 100%;
    font-family: inherit;
    font-size: .8125rem;
    padding: .55rem .75rem;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: .75rem;
    color: #334155;
}

.blok-input:focus {
    outline: none;
    box-shadow: 0 0 0 2px #0f172a;
}

.blok-galat {
    margin-top: .3rem;
    font-size: .6875rem;
    color: #dc2626;
    font-weight: 600;
}

.blok-bantu {
    margin-top: .3rem;
    font-size: .6875rem;
    color: #94a3b8;
    line-height: 1.5;
}
</style>
