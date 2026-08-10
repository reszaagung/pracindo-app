<template>
    <div class="flex flex-col w-full animate-fade-in relative">
        <!-- Header -->
        <div class="mb-4 md:mb-6 flex flex-col md:flex-row justify-between items-start md:items-end gap-4 md:gap-0">
            <div>
                <p class="text-xs text-slate-400 mb-1">
                    <router-link to="/" class="hover:text-slate-700 transition-colors">Dashboard</router-link> ›
                    <router-link to="/accounting/invoice" class="hover:text-slate-700 transition-colors">Piutang
                        (AR)</router-link> › Buat Invoice
                </p>
                <div class="flex items-center gap-3">
                    <h2 class="text-xl md:text-2xl font-bold text-slate-800 tracking-tight">Faktur Tagihan (Invoice)
                    </h2>
                    <span
                        class="bg-indigo-100 text-indigo-700 text-[10px] font-bold px-2.5 py-1 rounded-full tracking-wide">PENAGIHAN</span>
                </div>
            </div>
        </div>

        <!-- Notifikasi Error -->
        <div v-if="pesanError"
            class="mb-4 p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-600 font-medium flex items-start gap-3">
            <i class="pi pi-exclamation-triangle mt-0.5"></i>
            <span>{{ pesanError }}</span>
        </div>

        <form @submit.prevent="terbitkanInvoice"
            class="bg-white border border-slate-200 rounded-[24px] p-4 md:p-8 shadow-[0_4px_20px_rgba(0,0,0,0.02)] w-full">

            <!-- Grid Atas: Informasi Dokumen & Waktu -->
            <div class="grid grid-cols-1 md:grid-cols-4 gap-4 md:gap-6 mb-8 border-b border-slate-100 pb-8">
                <div class="flex flex-col gap-2">
                    <label class="text-xs font-bold text-slate-700">No. Invoice (Preview)</label>
                    <input :value="previewNomorInvoice" type="text" readonly
                        class="px-4 py-2.5 bg-slate-100 border border-slate-200 rounded-xl focus:outline-none text-sm text-slate-500 font-semibold cursor-not-allowed" />
                </div>
                <div class="flex flex-col gap-2">
                    <label class="text-xs font-bold text-slate-700">Referensi SO (Wajib)</label>
                    <input v-model="form.referensi_so" type="text" required placeholder="Cari / Ketik No. SO..."
                        class="px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm text-slate-800 uppercase" />
                </div>
                <div class="flex flex-col gap-2">
                    <label class="text-xs font-bold text-slate-700">Tanggal Terbit</label>
                    <input v-model="form.tanggal_terbit" type="date" required
                        class="px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm text-slate-800" />
                </div>
                <div class="flex flex-col gap-2">
                    <label class="text-xs font-bold text-indigo-700">Jatuh Tempo (Due Date)</label>
                    <input v-model="form.jatuh_tempo" type="date" required
                        class="px-4 py-2.5 bg-indigo-50 border border-indigo-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm text-indigo-900 font-bold shadow-inner" />
                </div>
            </div>

            <!-- Rincian Penagihan & Pembayaran -->
            <div class="flex flex-col md:flex-row gap-8">

                <!-- Kiri: Catatan & Rekening (60%) -->
                <div class="w-full md:w-3/5 flex flex-col gap-6">
                    <div>
                        <label class="text-xs font-bold text-slate-700 block mb-2">Pilih Rekening Pembayaran
                            (Bank)</label>
                        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                            <label v-for="rek in daftarRekening" :key="rek.id"
                                :class="['cursor-pointer border p-4 rounded-xl transition-all', form.rekening_id === rek.id ? 'border-indigo-500 bg-indigo-50 ring-1 ring-indigo-500' : 'border-slate-200 bg-white hover:bg-slate-50']">
                                <input type="radio" v-model="form.rekening_id" :value="rek.id" class="hidden">
                                <div class="flex justify-between items-center mb-1">
                                    <span class="font-black text-slate-800">{{ rek.nama_bank }}</span>
                                    <i class="pi pi-check-circle text-indigo-600"
                                        v-if="form.rekening_id === rek.id"></i>
                                </div>
                                <p class="text-sm font-semibold tracking-widest text-slate-600">{{ rek.nomor }}</p>
                                <p class="text-xs text-slate-500 mt-1">A.N: {{ rek.atas_nama }}</p>
                            </label>
                        </div>
                    </div>

                    <div>
                        <label class="text-xs font-bold text-slate-700 block mb-2">Syarat & Ketentuan (Term of
                            Payment)</label>
                        <textarea v-model="form.catatan" rows="4"
                            placeholder="Misal: Pembayaran ditransfer lunas sebelum jatuh tempo. Keterlambatan dikenakan denda..."
                            class="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none text-slate-800"></textarea>
                    </div>
                </div>

                <!-- Kanan: Kalkulasi Tagihan (40%) -->
                <div
                    class="w-full md:w-2/5 bg-slate-50 rounded-2xl p-6 border border-slate-100 flex flex-col justify-between">
                    <div>
                        <h3 class="text-sm font-bold text-slate-800 mb-4 pb-2 border-b border-slate-200">Kalkulasi
                            Tagihan SO</h3>

                        <!-- Input Nominal Manual untuk contoh (Aslinya ditarik otomatis dari SO) -->
                        <div class="mb-4">
                            <label class="text-xs text-slate-500 font-bold block mb-1">Nominal Subtotal SO (Rp)</label>
                            <input v-model.number="form.subtotal" type="number"
                                class="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm text-right focus:ring-2 focus:ring-indigo-500"
                                placeholder="0">
                        </div>

                        <div class="flex items-center gap-2 mb-4">
                            <input type="checkbox" id="ppn" v-model="form.pakai_ppn"
                                class="w-4 h-4 rounded text-indigo-600">
                            <label for="ppn" class="text-xs font-bold text-slate-700 cursor-pointer">Tambahkan PPN
                                11%</label>
                        </div>

                        <div class="flex justify-between items-center text-sm mb-2">
                            <span class="text-slate-500">Subtotal</span>
                            <span class="font-bold text-slate-700">Rp {{ formatRupiah(form.subtotal) }}</span>
                        </div>

                        <div v-if="form.pakai_ppn" class="flex justify-between items-center text-sm animate-fade-in">
                            <span class="text-indigo-600 font-semibold">PPN (11%)</span>
                            <span class="font-bold text-indigo-700">Rp {{ formatRupiah(nominalPpn) }}</span>
                        </div>
                    </div>

                    <div class="mt-6 pt-4 border-t border-slate-200">
                        <div class="flex justify-between items-end mb-6">
                            <span class="text-xs font-bold text-slate-400 uppercase tracking-wider">Total Tagihan</span>
                            <span class="text-3xl font-black text-slate-800">Rp {{ formatRupiah(grandTotal) }}</span>
                        </div>

                        <button type="submit" :disabled="sedangProses || grandTotal <= 0"
                            class="w-full justify-center px-6 py-4 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 text-white font-bold rounded-xl shadow-[0_4px_15px_rgba(79,70,229,0.3)] transition-all flex items-center gap-2 cursor-pointer disabled:cursor-not-allowed">
                            <i class="pi" :class="sedangProses ? 'pi-spin pi-spinner' : 'pi-receipt'"></i>
                            {{ sedangProses ? 'Memproses...' : 'Terbitkan Invoice' }}
                        </button>
                    </div>
                </div>

            </div>
        </form>
    </div>
</template>

<script setup>
import { reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useInvoice } from '@/features/accounting/composables/useInvoice'

const router = useRouter()
const { sedangProses, pesanError, previewNomorInvoice, daftarRekening, simpanInvoice } = useInvoice()

const hariIni = () => {
    const t = new Date(Date.now() - new Date().getTimezoneOffset() * 60_000)
    return t.toISOString().slice(0, 10)
}

// Set jatuh tempo default 14 hari dari sekarang
const hariJatuhTempo = () => {
    const t = new Date(Date.now() - new Date().getTimezoneOffset() * 60_000)
    t.setDate(t.getDate() + 14)
    return t.toISOString().slice(0, 10)
}

const form = reactive({
    referensi_so: '',
    tanggal_terbit: hariIni(),
    jatuh_tempo: hariJatuhTempo(),
    rekening_id: null,
    catatan: 'Harap melakukan pembayaran tepat waktu sesuai tagihan di atas. Terima kasih.',
    subtotal: 0,
    pakai_ppn: false
})

onMounted(() => {
    if (daftarRekening.value.length > 0) {
        form.rekening_id = daftarRekening.value[0].id
    }
})

// Kalkulasi
const nominalPpn = computed(() => form.pakai_ppn ? (form.subtotal * 0.11) : 0)
const grandTotal = computed(() => form.subtotal + nominalPpn.value)

const formatRupiah = (angka) => {
    return new Intl.NumberFormat('id-ID', { minimumFractionDigits: 0 }).format(angka || 0)
}

const terbitkanInvoice = async () => {
    if (!form.rekening_id) {
        alert("Pilih rekening bank tujuan pembayaran terlebih dahulu.")
        return
    }

    const payload = {
        referensi_so: form.referensi_so,
        tanggal_terbit: form.tanggal_terbit,
        jatuh_tempo: form.jatuh_tempo,
        rekening_id: form.rekening_id,
        catatan: form.catatan,
        subtotal: form.subtotal,
        ppn: nominalPpn.value,
        grand_total: grandTotal.value
    }

    const hasil = await simpanInvoice(payload)
    if (hasil.success) {
        alert("Invoice berhasil diterbitkan!")
        router.push('/accounting/invoice') // Kembali ke daftar list Invoice
    }
}
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
</style>