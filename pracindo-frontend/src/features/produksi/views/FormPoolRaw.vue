<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useFormPoolRaw } from '../composables/useFormPoolRaw'

const emit = defineEmits(['tampil-notifikasi'])
const router = useRouter()

// daftarGrupBahan telah dihapus karena grup dideteksi otomatis oleh otak composable

const {
    form, bahan, opsi, memuat, galatServer, galat, bisaKirim, totalBahan,
    opsiEntitasAsal, grupBahanId, // <-- grupBahanId dipanggil di sini
    muatDataAwal, stokById, opsiUntukBaris, tambahBaris, hapusBaris, kirim, reset,
    tampilkan, galatBaris
} = useFormPoolRaw((hasil) => {
    emit('tampil-notifikasi', 'Bahan berhasil ditransfer dan dilebur ke Pool!', 'sukses')
    router.push('/produksi/mixing')
}) // Parameter daftar grup dihapus

const formatAngka = (n) => Number(n || 0).toLocaleString('id-ID', { minimumFractionDigits: 3, maximumFractionDigits: 3 })

onMounted(() => {
    muatDataAwal()
})
</script>

<template>
    <section class="fp">
        <header class="fp__head">
            <h1>Transfer ke Pool (Peleburan Entitas)</h1>
            <p>Pindahkan bahan mentah dari Gudang ke Pool. Pilih entitas pemilik terlebih dahulu untuk memotong stok
                dengan presisi.</p>
        </header>

        <div v-if="galatServer" class="pita pita--galat" role="alert">
            <strong>Gagal Memproses: {{ galatServer.message || 'Terjadi kesalahan pada server.' }}</strong>
            <p class="pita__catatan">Silakan periksa kembali input Anda atau muat ulang halaman.</p>
        </div>

        <fieldset class="blok">
            <legend>Alur Transfer (Sumber & Tujuan)</legend>
            <div class="grid grid--3">
                <!-- Pilihan Entitas Asal (Murni Entitas) -->
                <label class="bidang">
                    <span>Entitas Asal (Pemilik)</span>
                    <select v-model="form.entitas_asal_id" :disabled="memuat.awal">
                        <option value="">-- pilih entitas --</option>
                        <option v-for="e in opsiEntitasAsal" :key="e.id" :value="e.id">
                            {{ e.kode }}
                        </option>
                    </select>
                    <em v-if="tampilkan('entitas_asal_id')">{{ galat.entitas_asal_id }}</em>
                </label>

                <!-- Pool Tujuan (Teks Otomatis, Bukan Dropdown) -->
                <label class="bidang">
                    <span>Pool Tujuan (Peleburan)</span>
                    <div class="val-teks"
                        style="padding: 0.4375rem 0.5rem; border: 1px solid var(--line); border-radius: 2px; background: #eef1f6; color: var(--ink-2); height: 100%; display: flex; align-items: center;">
                        <template v-if="grupBahanId">
                            <i class="pi pi-check-circle mr-2" style="color: #16a34a;"></i>
                            <b>{{opsi.stokGudang.find(s => (s.grup_bahan_id || (s.grup_bahan && s.grup_bahan.id) ||
                                s.grup_bahan) === grupBahanId)?.grup_bahan_kode || 'Pool Sesuai Grup' }}</b>
                        </template>
                        <template v-else>
                            <span style="opacity: 0.6;">Pilih bahan di bawah...</span>
                        </template>
                    </div>
                </label>

                <label class="bidang">
                    <span>Tanggal Transfer</span>
                    <input v-model="form.tanggal" type="date" />
                    <em v-if="tampilkan('tanggal')">{{ galat.tanggal }}</em>
                </label>
            </div>

            <div class="grid grid--1 mt-4">
                <label class="bidang">
                    <span>Catatan Transfer <i>opsional</i></span>
                    <input v-model="form.catatan" type="text"
                        placeholder="Contoh: Persiapan untuk batch produksi sore..." autocomplete="off" />
                </label>
            </div>
        </fieldset>

        <fieldset class="blok">
            <legend>Daftar Bahan Mentah</legend>

            <div v-if="memuat.awal" class="p-4 text-center text-slate-500">
                <i class="pi pi-spin pi-spinner"></i> Memuat stok Bahan Mentah...
            </div>
            <div v-else-if="opsi.stokGudang.length === 0" class="kosong">
                Tidak ada stok Bahan Mentah (RAW) yang tersedia saat ini.
            </div>
            <div v-else-if="!form.entitas_asal_id" class="kosong"
                style="border-left-color: var(--aksi); background: #f5f8ff;">
                Pilih <b>Entitas Asal</b> di atas untuk menampilkan daftar bahan yang bisa ditransfer.
            </div>

            <template v-else>
                <table class="tabel">
                    <thead>
                        <tr>
                            <th class="w-num">#</th>
                            <th>Material Terpilih</th>
                            <th class="w-qty">Tersedia</th>
                            <th class="w-qty">Ditransfer</th>
                            <th class="w-aksi"><span class="sr">Aksi</span></th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="(b, i) in bahan" :key="i" :class="{ 'is-galat': galatBaris(i) }">
                            <td class="w-num">{{ i + 1 }}</td>
                            <td>
                                <select v-model="b.stok_id">
                                    <option value="">-- pilih material --</option>
                                    <option v-for="s in opsiUntukBaris(i)" :key="s.id" :value="s.id">
                                        {{ s.produk?.kode || s.produk_kode }}
                                    </option>
                                </select>
                                <em v-if="galatBaris(i)">{{ galatBaris(i) }}</em>
                            </td>
                            <td class="w-qty num">{{ b.stok_id ? formatAngka(stokById(b.stok_id)?.qty) : '-' }}</td>
                            <td class="w-qty">
                                <input v-model="b.qty" type="text" inputmode="decimal" class="num" placeholder="0.000"
                                    :disabled="!b.stok_id" />
                            </td>
                            <td class="w-aksi">
                                <button type="button" class="tbl-btn" @click="hapusBaris(i)"
                                    :disabled="bahan.length <= 1">
                                    <i class="pi pi-trash"></i>
                                </button>
                            </td>
                        </tr>
                    </tbody>
                    <tfoot>
                        <tr>
                            <td colspan="3">Total Massa Dipindahkan</td>
                            <td class="num tebal">{{ formatAngka(totalBahan) }}</td>
                            <td></td>
                        </tr>
                    </tfoot>
                </table>
                <button type="button" class="tautan" @click="tambahBaris">+ Tambah Baris Bahan</button>
                <em v-if="tampilkan('baris')" class="blok__galat">{{ galat.baris }}</em>
            </template>
        </fieldset>

        <footer class="fp__kaki">
            <button type="button" class="btn btn--sunyi" @click="reset" :disabled="memuat.kirim">Reset Form</button>
            <button type="button" class="btn btn--utama" @click="kirim" :disabled="!bisaKirim || memuat.kirim">
                <i v-if="memuat.kirim" class="pi pi-spin pi-spinner mr-2"></i>
                {{ memuat.kirim ? 'Mengeksekusi...' : 'Transfer & Leburkan ke Pool' }}
            </button>
        </footer>
    </section>
</template>

<style scoped>
/* Gunakan CSS ISA-101 yang sama persis dengan FormMixing.vue */
.fp {
    --ink: #1e2126;
    --ink-2: #5a6270;
    --line: #c9cdd4;
    --line-2: #e4e7eb;
    --surface: #ffffff;
    --field: #f4f5f7;
    --aksi: #2e4a8f;
    --tolak: #a32020;
    --tolak-bg: #fdf0f0;
    max-width: 60rem;
    margin: 0 auto;
    padding: 1.5rem 1.25rem 3rem;
    color: var(--ink);
    font: 400 0.9375rem/1.5 system-ui, sans-serif;
}

.fp__head h1 {
    margin: 0;
    font-size: 1.375rem;
    font-weight: 650;
}

.fp__head p {
    margin: 0.25rem 0 1.5rem;
    color: var(--ink-2);
    font-size: 0.875rem;
}

.blok {
    border: 1px solid var(--line);
    border-radius: 3px;
    background: var(--surface);
    padding: 1rem 1.125rem 1.25rem;
    margin: 0 0 1rem;
}

.blok legend {
    padding: 0 0.5rem;
    margin-left: -0.25rem;
    font-size: 0.75rem;
    font-weight: 650;
    color: var(--ink-2);
    text-transform: uppercase;
}

.grid {
    display: grid;
    gap: 0.875rem;
}

.grid--1 {
    grid-template-columns: 1fr;
}

.grid--2 {
    grid-template-columns: repeat(2, minmax(0, 1fr));
}

/* PENAMBAHAN GRID 3 KOLOM */
.grid--3 {
    grid-template-columns: repeat(3, minmax(0, 1fr));
}

.mt-4 {
    margin-top: 1rem;
}

.bidang {
    display: flex;
    flex-direction: column;
    gap: 0.3125rem;
}

.bidang>span {
    font-size: 0.8125rem;
    font-weight: 550;
}

.bidang>span i {
    font-style: normal;
    font-weight: 400;
    color: var(--ink-2);
}

.bidang em,
.tabel em,
.blok__galat {
    font-style: normal;
    font-size: 0.75rem;
    color: var(--tolak);
}

.blok__galat {
    display: block;
    margin-top: 0.5rem;
}

input[type="text"],
input[type="date"],
select {
    width: 100%;
    padding: 0.4375rem 0.5rem;
    border: 1px solid var(--line);
    border-radius: 2px;
    background: var(--field);
    color: inherit;
    font: inherit;
    font-size: 0.875rem;
}

input:focus-visible,
select:focus-visible,
button:focus-visible {
    outline: 2px solid var(--aksi);
    outline-offset: 1px;
}

input:disabled {
    background: #eceef1;
    color: #9aa1ac;
}

.tabel {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.875rem;
}

.tabel th {
    text-align: left;
    font-size: 0.6875rem;
    font-weight: 650;
    text-transform: uppercase;
    color: var(--ink-2);
    padding: 0 0.5rem 0.375rem;
    border-bottom: 1px solid var(--line);
}

.tabel td {
    padding: 0.375rem 0.5rem;
    vertical-align: top;
    border-bottom: 1px solid var(--line-2);
}

.tabel tfoot td {
    border-bottom: none;
    border-top: 2px solid var(--line);
    padding-top: 0.5rem;
}

.tabel tr.is-galat td {
    background: var(--tolak-bg);
}

.num {
    text-align: right;
    font-variant-numeric: tabular-nums;
}

.tebal {
    font-weight: 650;
}

.w-num {
    width: 3.5rem;
    color: var(--ink-2);
}

.w-qty {
    width: 8.5rem;
    text-align: right;
}

.w-aksi {
    width: 2.25rem;
    text-align: center;
}

.tbl-btn {
    width: 1.75rem;
    height: 1.75rem;
    line-height: 1;
    border: 1px solid var(--line);
    border-radius: 2px;
    background: var(--surface);
    color: var(--ink-2);
    cursor: pointer;
}

.tbl-btn:disabled {
    opacity: 0.35;
    cursor: not-allowed;
}

.tautan {
    margin-top: 0.625rem;
    padding: 0;
    border: 0;
    background: none;
    color: var(--aksi);
    font: inherit;
    font-size: 0.8125rem;
    font-weight: 550;
    cursor: pointer;
}

.kosong {
    margin: 0 0 0.75rem;
    padding: 0.625rem 0.75rem;
    background: var(--field);
    border-left: 3px solid var(--line);
    font-size: 0.8125rem;
    color: var(--ink-2);
}

.pita {
    padding: 0.75rem 0.875rem;
    border-radius: 2px;
    margin-bottom: 1rem;
    font-size: 0.8125rem;
}

.pita--galat {
    background: var(--tolak-bg);
    border-left: 3px solid var(--tolak);
    color: var(--tolak);
}

.fp__kaki {
    display: flex;
    justify-content: flex-end;
    gap: 0.625rem;
    margin-top: 1.25rem;
}

.btn {
    padding: 0.5rem 1.125rem;
    border-radius: 2px;
    font: inherit;
    font-size: 0.875rem;
    font-weight: 600;
    cursor: pointer;
    display: flex;
    align-items: center;
}

.btn--utama {
    background: var(--aksi);
    border: 1px solid var(--aksi);
    color: #fff;
}

.btn--sunyi {
    background: var(--surface);
    border: 1px solid var(--line);
    color: var(--ink);
}

.btn:disabled {
    opacity: 0.45;
    cursor: not-allowed;
}

.sr {
    position: absolute;
    width: 1px;
    height: 1px;
    overflow: hidden;
    clip: rect(0 0 0 0);
    white-space: nowrap;
}

.mr-2 {
    margin-right: 0.5rem;
}

/* RESPONSIVE AGAR GRID MENJADI 1 KOLOM DI HP */
@media (max-width: 40rem) {

    .grid--2,
    .grid--3 {
        grid-template-columns: 1fr;
    }
}
</style>