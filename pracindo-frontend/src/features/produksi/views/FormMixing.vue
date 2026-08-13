<!--
  FormMixing.vue
  
  Antarmuka untuk inisiasi batch pengadonan (Produksi & R&D).
  Sepenuhnya tersambung dengan API backend melalui useFormMixing.js.
  Dilengkapi dengan validasi kapasitas dan dukungan Idempotency Key.
-->
<script setup>
import { onMounted } from 'vue'
import { useFormMixing } from '../composables/useFormMixing'

const emit = defineEmits(['tersimpan'])

// Karena daftar Pool/Grup Bahan biasanya statis atau dikelola terpisah,
// kita bisa menginjeksinya sebagai opsi referensi awal.
const daftarGrupBahan = [
    { id: 1, kode: 'POOL-PRODUKSI', nama: 'Pool Utama Produksi' },
    { id: 2, kode: 'POOL-RND', nama: 'Pool Eksperimen R&D' },
]

// Panggil composable dan destructure semua properti reaktif & fungsi
const {
    form,
    bahan,
    opsi,
    memuat,
    galatServer,
    galat,
    peringatan,
    bisaKirim,
    opsiProdukJadi,
    kebutuhanResep,
    maksimum,
    totalBahan,
    targetHasil,
    susut,
    muatDataAwal,
    stokById,
    opsiUntukBaris,
    tambahBaris,
    hapusBaris,
    kirim,
    reset,
    tampil,
    tampilkan,
    galatBaris,
} = useFormMixing(emit, { grupBahan: daftarGrupBahan })

onMounted(() => {
    muatDataAwal()
})
</script>

<template>
    <section class="fp">
        <header class="fp__head">
            <h1>Form Pengadonan (Mixing)</h1>
            <p>Inisiasi batch pengadonan baru. Pemakaian bahan akan dicatat di lapis POOL saat sesi berjalan.</p>
        </header>

        <!-- ============ BANNER GALAT SERVER ============ -->
        <div v-if="galatServer" class="pita pita--galat" role="alert">
            <strong>Gagal Memproses: {{ galatServer.message }}</strong>
            <ul v-if="galatServer.perField && Object.keys(galatServer.perField).length > 0">
                <li v-for="(v, k) in galatServer.perField" :key="k">
                    {{ k }}: {{ v }}
                </li>
            </ul>
            <p class="pita__catatan">Kirim ulang aman — kunci idempotensi mencegah duplikasi batch.</p>
        </div>

        <!-- ============ IDENTITAS BATCH ============ -->
        <fieldset class="blok">
            <legend>Identitas Batch Adonan</legend>

            <!-- Mode Sesi -->
            <div class="pilihan mb-4" role="radiogroup" aria-label="Mode Sesi">
                <label :class="['pilihan__opsi', { 'is-aktif': form.jenis_sesi === 'PRODUKSI' }]">
                    <input type="radio" value="PRODUKSI" v-model="form.jenis_sesi" />
                    <span>PRODUKSI (Resep Baku)</span>
                </label>
                <label :class="['pilihan__opsi', { 'is-aktif': form.jenis_sesi === 'RND' }]">
                    <input type="radio" value="RND" v-model="form.jenis_sesi" />
                    <span>R&D (Eksperimen Manual)</span>
                </label>
            </div>

            <div class="grid grid--3">
                <label class="bidang">
                    <span>Pool Bahan (Grup Asal)</span>
                    <select v-model="form.grup_bahan_id" :disabled="memuat.grup">
                        <option value="">-- pilih pool --</option>
                        <option v-for="g in opsi.grup" :key="g.id" :value="g.id">
                            {{ g.kode }} — {{ g.nama }}
                        </option>
                    </select>
                    <em v-if="tampilkan('grup_bahan_id')">{{ galat.grup_bahan_id }}</em>
                </label>

                <label class="bidang">
                    <span>Tanggal Sesi</span>
                    <input v-model="form.tanggal" type="date" />
                    <em v-if="tampilkan('tanggal')">{{ galat.tanggal }}</em>
                </label>

                <label class="bidang">
                    <span>Resep Adonan</span>
                    <select v-model="form.resep_id" :disabled="form.jenis_sesi === 'RND' || memuat.awal">
                        <option value="">-- pilih resep --</option>
                        <option v-for="r in opsi.resep" :key="r.id" :value="r.id">
                            {{ r.kode }} — {{ r.nama }}
                        </option>
                    </select>
                    <em v-if="tampilkan('resep_id')">{{ galat.resep_id }}</em>
                </label>
            </div>

            <!-- Khusus R&D: Pilih Target Produk Jadi -->
            <div v-if="form.jenis_sesi === 'RND'" class="grid grid--1" style="margin-top: 0.875rem;">
                <label class="bidang">
                    <span>Proyeksi Produk Target (R&D)</span>
                    <select v-model="form.produk_jadi_id">
                        <option value="">-- pilih produk --</option>
                        <option v-for="p in opsiProdukJadi" :key="p.id" :value="p.id">
                            {{ p.kode }} — {{ p.nama }}
                        </option>
                    </select>
                    <em v-if="tampilkan('produk_jadi_id')">{{ galat.produk_jadi_id }}</em>
                </label>
            </div>

            <div class="grid grid--1" style="margin-top: 0.875rem;">
                <label class="bidang">
                    <span>Catatan Operator <i>opsional</i></span>
                    <input v-model="form.catatan" type="text" placeholder="Contoh: Kondisi suhu ruangan normal..."
                        autocomplete="off" />
                </label>
            </div>
        </fieldset>

        <!-- ============ TARGET HASIL ============ -->
        <!-- Dipindah ke atas tabel bahan karena dalam mode PRODUKSI, target menentukan BOM -->
        <fieldset class="blok">
            <legend>Target Produksi</legend>

            <label class="bidang bidang--sempit">
                <span>Target Output Hasil (kg)</span>
                <input v-model="form.target_hasil" type="text" inputmode="decimal" class="num num--besar"
                    placeholder="0.000" />
                <em v-if="tampilkan('target_hasil')">{{ galat.target_hasil }}</em>

                <small v-if="maksimum > 0 && form.jenis_sesi === 'PRODUKSI'" class="mt-1" style="color: var(--aksi)">
                    Maksimum output yang bisa dibuat: <b>{{ tampil(maksimum) }} kg</b>
                </small>
            </label>

            <div v-if="memuat.kapasitas" class="mt-2 text-sm text-slate-500">
                <i class="pi pi-spin pi-spinner"></i> Mengkalkulasi kapasitas bahan di pool...
            </div>
        </fieldset>

        <!-- ============ BAHAN BAKU (BOM VS MANUAL) ============ -->
        <fieldset class="blok">
            <legend>Komposisi Bahan Baku</legend>

            <!-- TABEL PRODUKSI (Otomatis & Read-Only) -->
            <template v-if="form.jenis_sesi === 'PRODUKSI'">
                <p v-if="!form.resep_id || !targetHasil" class="kosong">
                    Pilih resep dan isi target hasil terlebih dahulu untuk melihat Bill of Materials (BOM).
                </p>
                <table v-else class="tabel">
                    <thead>
                        <tr>
                            <th>Material</th>
                            <th class="w-qty">Dibutuhkan</th>
                            <th class="w-qty">Tersedia (Pool)</th>
                            <th class="w-num">Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="r in kebutuhanResep" :key="r.bahan_id" :class="{ 'is-galat': !r.cukup }">
                            <td>{{ r.kode }}</td>
                            <td class="w-qty num">{{ tampil(r.butuh) }}</td>
                            <td class="w-qty num">{{ tampil(r.tersedia) }}</td>
                            <td class="w-num">
                                <i v-if="r.cukup" class="pi pi-check-circle" style="color: #10b981"></i>
                                <i v-else class="pi pi-times-circle" style="color: var(--tolak)"></i>
                            </td>
                        </tr>
                    </tbody>
                    <tfoot>
                        <tr>
                            <td colspan="1">Total Input Bahan</td>
                            <td class="num tebal">{{ tampil(totalBahan) }}</td>
                            <td colspan="2"></td>
                        </tr>
                    </tfoot>
                </table>
            </template>

            <!-- TABEL R&D (Input Manual) -->
            <template v-else>
                <table class="tabel">
                    <thead>
                        <tr>
                            <th class="w-num">#</th>
                            <th>Material di Pool</th>
                            <th class="w-qty">Tersedia</th>
                            <th class="w-qty">Dimasukkan</th>
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
                                        {{ s.produk_kode }}
                                        <template v-if="s.tangki_kode"> — {{ s.tangki_kode }}</template>
                                    </option>
                                </select>
                                <em v-if="galatBaris(i)">{{ galatBaris(i) }}</em>
                            </td>
                            <td class="w-qty num">{{ b.stok_id ? tampil(stokById(b.stok_id)?.qty) : '-' }}</td>
                            <td class="w-qty">
                                <input v-model="b.qty" type="text" inputmode="decimal" class="num" placeholder="0.000"
                                    :disabled="!b.stok_id" />
                            </td>
                            <td class="w-aksi">
                                <button type="button" class="tbl-btn" @click="hapusBaris(i)"
                                    :disabled="bahan.length <= 1"><i class="pi pi-trash"></i></button>
                            </td>
                        </tr>
                    </tbody>
                    <tfoot>
                        <tr>
                            <td colspan="3">Total Input Bahan</td>
                            <td class="num tebal">{{ tampil(totalBahan) }}</td>
                            <td></td>
                        </tr>
                    </tfoot>
                </table>
                <button type="button" class="tautan" @click="tambahBaris">+ Tambah Bahan Manual</button>
                <em v-if="tampilkan('baris')" class="blok__galat">{{ galat.baris }}</em>
            </template>

            <!-- Peringatan Neraca & Susut -->
            <div class="neraca" v-if="totalBahan > 0">
                <dl class="neraca__angka" style="grid-template-columns: repeat(3, minmax(0, 1fr));">
                    <div>
                        <dt>Total Input</dt>
                        <dd class="num">{{ tampil(totalBahan) }}</dd>
                    </div>
                    <div>
                        <dt>Target Output</dt>
                        <dd class="num">{{ tampil(targetHasil) }}</dd>
                    </div>
                    <div>
                        <dt>Est. Susut Penguapan</dt>
                        <dd class="num" :class="{ 'negatif': susut < 0 }">{{ tampil(susut) }}</dd>
                    </div>
                </dl>
            </div>

            <div v-if="peringatan.length" class="pita pita--awas">
                <p v-for="(p, i) in peringatan" :key="i">{{ p }}</p>
            </div>
        </fieldset>

        <!-- ============ TANGKI TUJUAN ============ -->
        <fieldset class="blok">
            <legend>Wadah / Tangki Tujuan</legend>
            <div class="pilihan" role="radiogroup" aria-label="Mode tangki">
                <label :class="['pilihan__opsi', { 'is-aktif': form.mode_tangki === 'ada' }]">
                    <input type="radio" value="ada" v-model="form.mode_tangki" />
                    <span>Tangki WIP Tersedia</span>
                </label>
                <label :class="['pilihan__opsi', { 'is-aktif': form.mode_tangki === 'baru' }]">
                    <input type="radio" value="baru" v-model="form.mode_tangki" />
                    <span>Daftarkan Tangki Baru</span>
                </label>
            </div>

            <template v-if="form.mode_tangki === 'ada'">
                <label class="bidang">
                    <span>Pilih Tangki</span>
                    <select v-model="form.tangki_hasil_id" :disabled="!form.grup_bahan_id || memuat.grup">
                        <option value="">-- pilih tangki --</option>
                        <option v-for="t in opsi.tangki" :key="t.id" :value="t.id">
                            {{ t.kode }} — {{ t.nama }} (sisa ruang: {{ tampil(t.ruang_kosong_kg) }} kg)
                        </option>
                    </select>
                    <em v-if="tampilkan('tangki_hasil_id')">{{ galat.tangki_hasil_id }}</em>
                    <small v-if="!form.grup_bahan_id">Pilih Pool Bahan di atas terlebih dahulu untuk memuat daftar
                        tangki.</small>
                </label>
            </template>

            <div v-else class="grid grid--3">
                <label class="bidang">
                    <span>Kode</span>
                    <input v-model="form.tangki_baru.kode" type="text" placeholder="TK-09" autocomplete="off" />
                    <em v-if="tampilkan('tangki_baru_kode')">{{ galat.tangki_baru_kode }}</em>
                </label>
                <label class="bidang">
                    <span>Nama</span>
                    <input v-model="form.tangki_baru.nama" type="text" placeholder="Tangki simpan 9"
                        autocomplete="off" />
                    <em v-if="tampilkan('tangki_baru_nama')">{{ galat.tangki_baru_nama }}</em>
                </label>
                <label class="bidang">
                    <span>Kapasitas Max (kg)</span>
                    <input v-model="form.tangki_baru.kapasitas_kg" type="text" inputmode="decimal" class="num"
                        placeholder="12000.000" />
                    <em v-if="tampilkan('tangki_baru_kapasitas')">{{ galat.tangki_baru_kapasitas }}</em>
                </label>
            </div>
        </fieldset>

        <footer class="fp__kaki">
            <button type="button" class="btn btn--sunyi" @click="reset" :disabled="memuat.kirim">Batalkan</button>
            <button type="button" class="btn btn--utama" @click="kirim" :disabled="!bisaKirim || memuat.kirim">
                <i v-if="memuat.kirim" class="pi pi-spin pi-spinner mr-2"></i>
                {{ memuat.kirim ? 'Memproses Sesi...' : 'Buat Sesi Pengadonan' }}
            </button>
        </footer>
    </section>
</template>

<style scoped>
/*
  ISA-101: permukaan netral, warna hanya membawa arti. Indigo untuk aksi,
  merah untuk penolakan, kuning untuk peringatan.
  Angka selalu rata kanan dan tabular supaya digit sejajar antar baris.
*/
.fp {
    --ink: #1e2126;
    --ink-2: #5a6270;
    --line: #c9cdd4;
    --line-2: #e4e7eb;
    --surface: #ffffff;
    --field: #f4f5f7;
    --aksi: #2e4a8f;
    --awas: #8a6100;
    --awas-bg: #fdf6e3;
    --tolak: #a32020;
    --tolak-bg: #fdf0f0;
    max-width: 60rem;
    margin: 0 auto;
    padding: 1.5rem 1.25rem 3rem;
    color: var(--ink);
    font: 400 0.9375rem/1.5 system-ui, -apple-system, "Segoe UI", sans-serif;
}

.mb-4 {
    margin-bottom: 1rem;
}

.mr-2 {
    margin-right: 0.5rem;
}

.mt-1 {
    margin-top: 0.25rem;
    display: inline-block;
}

.fp__head h1 {
    margin: 0;
    font-size: 1.375rem;
    font-weight: 650;
    letter-spacing: -0.01em;
}

.fp__head p {
    margin: 0.25rem 0 1.5rem;
    color: var(--ink-2);
    font-size: 0.875rem;
}

/* --- blok --- */
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
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--ink-2);
}

.blok__galat {
    display: block;
    margin-top: 0.5rem;
}

.grid {
    display: grid;
    gap: 0.875rem;
}

.grid--2 {
    grid-template-columns: repeat(2, minmax(0, 1fr));
}

.grid--3 {
    grid-template-columns: repeat(3, minmax(0, 1fr));
}

.grid+.grid {
    margin-top: 0.875rem;
}

/* --- bidang isian --- */
.bidang {
    display: flex;
    flex-direction: column;
    gap: 0.3125rem;
}

.bidang--sempit {
    max-width: 16rem;
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

.bidang small {
    color: var(--ink-2);
    font-size: 0.75rem;
}

.bidang em,
.tabel em {
    font-style: normal;
    font-size: 0.75rem;
    color: var(--tolak);
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

input:disabled,
select:disabled {
    background: #eceef1;
    color: #9aa1ac;
}

.num {
    text-align: right;
    font-variant-numeric: tabular-nums;
}

.num--besar {
    font-size: 1.125rem;
    font-weight: 600;
    padding: 0.5rem;
}

.tebal {
    font-weight: 650;
}

.negatif {
    color: var(--tolak);
}

/* --- pilihan radio btn --- */
.pilihan {
    display: flex;
    gap: 0.5rem;
}

.pilihan__opsi {
    display: flex;
    align-items: center;
    gap: 0.4375rem;
    padding: 0.4375rem 0.75rem;
    border: 1px solid var(--line);
    border-radius: 2px;
    font-size: 0.8125rem;
    cursor: pointer;
}

.pilihan__opsi.is-aktif {
    border-color: var(--aksi);
    box-shadow: inset 0 0 0 1px var(--aksi);
    background-color: #f5f8ff;
}

.pilihan__opsi input {
    accent-color: var(--aksi);
}

/* --- tabel bahan --- */
.tabel {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.875rem;
}

.tabel th {
    text-align: left;
    font-size: 0.6875rem;
    font-weight: 650;
    letter-spacing: 0.06em;
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

.w-num {
    width: 3.5rem;
    color: var(--ink-2);
    font-variant-numeric: tabular-nums;
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
    font-size: 1rem;
    cursor: pointer;
}

.tbl-btn:disabled {
    opacity: 0.35;
    cursor: not-allowed;
}

.kosong {
    margin: 0 0 0.75rem;
    padding: 0.625rem 0.75rem;
    background: var(--field);
    border-left: 3px solid var(--line);
    font-size: 0.8125rem;
    color: var(--ink-2);
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

/* --- neraca massa --- */
.neraca {
    margin-top: 1.25rem;
}

.neraca__angka {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 0.75rem;
    margin: 0.625rem 0 0;
}

.neraca__angka dt {
    font-size: 0.6875rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--ink-2);
}

.neraca__angka dd {
    margin: 0.125rem 0 0;
    font-size: 1rem;
    font-weight: 600;
}

/* --- pita pesan (alert) --- */
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

.pita--awas {
    background: var(--awas-bg);
    border-left: 3px solid var(--awas);
    color: var(--awas);
    margin: 1rem 0 0;
}

.pita ul {
    margin: 0.375rem 0 0;
    padding-left: 1.125rem;
}

.pita p {
    margin: 0;
}

.pita p+p {
    margin-top: 0.25rem;
}

.pita__catatan {
    margin-top: 0.5rem;
    color: var(--ink-2);
}

/* --- kaki / aksi --- */
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

@media (max-width: 40rem) {

    .grid--2,
    .grid--3 {
        grid-template-columns: 1fr;
    }

    .neraca__angka {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .w-qty {
        width: 6rem;
    }
}
</style>