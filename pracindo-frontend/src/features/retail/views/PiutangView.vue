<script setup>
import { ref, onMounted } from 'vue'
import { usePiutang } from '../composables/usePiutang'
import dayjs from 'dayjs'

const { piutangList, fetchPiutang, prosesBayar, isLoading } = usePiutang()

const isModalOpen = ref(false)
const selectedPiutang = ref(null)
const form = ref({
    nominal: 0,
    metode_bayar: 'TUNAI'
})

onMounted(() => {
    fetchPiutang()
})

const formatTanggal = (date) => dayjs(date).format('DD MMM YYYY')

const openModal = (piutang) => {
    selectedPiutang.value = piutang
    form.value.nominal = Number(piutang.sisa_piutang)
    form.value.metode_bayar = 'TUNAI'
    isModalOpen.value = true
}

const closeModal = () => {
    isModalOpen.value = false
    selectedPiutang.value = null
}

const submitPembayaran = async () => {
    if (form.value.nominal <= 0 || form.value.nominal > Number(selectedPiutang.value.sisa_piutang)) {
        alert('Nominal tidak valid atau melebihi sisa tagihan!')
        return
    }

    const res = await prosesBayar(selectedPiutang.value.id, form.value)
    if (res.status === 'sukses') {
        alert('Pembayaran berhasil dicatat!')
        closeModal()
        fetchPiutang() // Refresh data
    } else {
        alert(`Gagal: ${res.pesan}`)
    }
}
</script>

<template>
    <div class="p-6 max-w-7xl mx-auto space-y-6">
        <header class="flex justify-between items-end border-b border-slate-200 pb-4">
            <div>
                <p class="text-sm text-slate-500 mb-1">Keuangan Cabang</p>
                <h1 class="text-2xl font-bold text-slate-800">Buku Piutang Pelanggan</h1>
            </div>
        </header>

        <div class="bg-white rounded-[20px] shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-slate-100 overflow-hidden">
            <table class="min-w-full divide-y divide-slate-200">
                <thead class="bg-slate-50">
                    <tr>
                        <th class="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase">Pelanggan</th>
                        <th class="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase">No. Struk</th>
                        <th class="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase">Jatuh Tempo</th>
                        <th class="px-6 py-4 text-right text-xs font-bold text-slate-500 uppercase">Sisa Tagihan</th>
                        <th class="px-6 py-4 text-center text-xs font-bold text-slate-500 uppercase">Status</th>
                        <th class="px-6 py-4 text-center text-xs font-bold text-slate-500 uppercase">Aksi</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-slate-100">
                    <tr v-if="isLoading" class="bg-white">
                        <td colspan="6" class="px-6 py-8 text-center text-slate-400">Memuat data...</td>
                    </tr>
                    <tr v-else-if="piutangList.length === 0" class="bg-white">
                        <td colspan="6" class="px-6 py-8 text-center text-slate-400">Belum ada data piutang pelanggan.</td>
                    </tr>

                    <tr v-for="p in piutangList" :key="p.id" class="hover:bg-slate-50 transition-colors">
                        <td class="px-6 py-4 whitespace-nowrap text-sm font-bold text-slate-800">{{ p.pelanggan_nama }}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm font-semibold text-blue-600">{{ p.nomor_struk }}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm">
                            <div class="flex flex-col">
                                <span class="font-medium text-slate-700">{{ formatTanggal(p.jatuh_tempo) }}</span>
                                <span v-if="p.status !== 'LUNAS'" class="text-xs font-bold"
                                      :class="p.sisa_hari_jatuh_tempo < 0 ? 'text-red-500' : (p.sisa_hari_jatuh_tempo <= 7 ? 'text-orange-500' : 'text-emerald-500')">
                                    {{ p.sisa_hari_jatuh_tempo < 0 ? `Lewat ${Math.abs(p.sisa_hari_jatuh_tempo)} Hari` : `${p.sisa_hari_jatuh_tempo} Hari Lagi` }}
                                </span>
                            </div>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm font-bold text-slate-800 text-right">
                            Rp {{ Number(p.sisa_piutang).toLocaleString('id-ID') }}
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-center">
                            <span :class="p.status === 'LUNAS' ? 'bg-emerald-100 text-emerald-700' : (p.status === 'MENCICIL' ? 'bg-blue-100 text-blue-700' : 'bg-orange-100 text-orange-700')" class="px-3 py-1 rounded-md text-xs font-bold">
                                {{ p.status }}
                            </span>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-center">
                            <button v-if="p.status !== 'LUNAS'" @click="openModal(p)" class="bg-slate-900 text-white px-4 py-2 rounded-lg text-xs font-bold hover:bg-slate-800 shadow transition-colors">
                                BAYAR
                            </button>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- Modal Pembayaran -->
        <div v-if="isModalOpen" class="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div class="bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden">
                <div class="p-5 border-b border-slate-100 flex justify-between items-center bg-slate-50">
                    <h3 class="font-bold text-lg text-slate-800">Proses Pembayaran</h3>
                    <button @click="closeModal" class="text-slate-400 hover:text-red-500 transition-colors"><i class="pi pi-times"></i></button>
                </div>
                <div class="p-6 space-y-4">
                    <div class="bg-blue-50 border border-blue-100 rounded-xl p-4 mb-4">
                        <p class="text-xs text-blue-600 font-semibold mb-1">Total Tagihan {{ selectedPiutang?.pelanggan_nama }}</p>
                        <p class="text-2xl font-bold text-slate-800">Rp {{ Number(selectedPiutang?.sisa_piutang).toLocaleString('id-ID') }}</p>
                    </div>

                    <div>
                        <label class="block text-sm font-semibold text-slate-700 mb-2">Nominal Bayar (Rp)</label>
                        <input v-model.number="form.nominal" type="number" class="w-full border border-slate-300 rounded-lg px-4 py-3 outline-none focus:border-blue-500 font-bold text-lg">
                    </div>
                    <div>
                        <label class="block text-sm font-semibold text-slate-700 mb-2">Metode Pembayaran</label>
                        <select v-model="form.metode_bayar" class="w-full border border-slate-300 rounded-lg px-4 py-3 outline-none focus:border-blue-500 font-medium">
                            <option value="TUNAI">Masuk Laci Kasir (TUNAI)</option>
                            <option value="TRANSFER">Transfer Bank</option>
                        </select>
                    </div>
                </div>
                <div class="p-5 border-t border-slate-100 flex gap-3">
                    <button @click="closeModal" class="flex-1 bg-slate-100 text-slate-600 font-bold py-3 rounded-xl hover:bg-slate-200 transition-colors">Batal</button>
                    <button @click="submitPembayaran" :disabled="isLoading" class="flex-1 bg-blue-600 text-white font-bold py-3 rounded-xl hover:bg-blue-700 transition-colors shadow-md flex justify-center items-center">
                        <i v-if="isLoading" class="pi pi-spinner pi-spin mr-2"></i>
                        <span>Simpan</span>
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>
