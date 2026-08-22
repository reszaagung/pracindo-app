<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAkuntansi } from '../composables/useAkuntansi'

const { akunList, fetchAkun, buatJurnal, isLoading } = useAkuntansi()

const form = ref({
    referensi: '',
    keterangan: '',
    items: [
        { akun_id: '', debit: 0, kredit: 0 },
        { akun_id: '', debit: 0, kredit: 0 }
    ]
})

onMounted(() => {
    fetchAkun()
})

const addRow = () => {
    form.value.items.push({ akun_id: '', debit: 0, kredit: 0 })
}

const removeRow = (index) => {
    if (form.value.items.length > 2) {
        form.value.items.splice(index, 1)
    }
}

// Perhitungan Otomatis Balance
const totalDebit = computed(() => form.value.items.reduce((sum, item) => sum + Number(item.debit || 0), 0))
const totalKredit = computed(() => form.value.items.reduce((sum, item) => sum + Number(item.kredit || 0), 0))
const isBalance = computed(() => totalDebit.value === totalKredit.value && totalDebit.value > 0)

const submitJurnal = async () => {
    if (!isBalance.value) {
        alert('Total Debit dan Kredit belum seimbang (balance)!')
        return
    }

    const res = await buatJurnal(form.value)
    if (res.status === 'sukses') {
        alert(`Jurnal Berhasil Disimpan!\nNomor: ${res.nomor_jurnal}`)
        form.value = {
            referensi: '', keterangan: '',
            items: [{ akun_id: '', debit: 0, kredit: 0 }, { akun_id: '', debit: 0, kredit: 0 }]
        }
    } else {
        alert(`Gagal: ${res.pesan}`)
    }
}
</script>

<template>
    <div class="p-6 max-w-7xl mx-auto space-y-6 pb-20">
        <header class="flex justify-between items-end border-b border-slate-200 pb-4">
            <div>
                <p class="text-sm text-slate-500 mb-1">Akuntansi</p>
                <h1 class="text-2xl font-bold text-slate-800">Entri Jurnal Umum</h1>
            </div>
        </header>

        <div class="bg-white rounded-[20px] p-6 shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-slate-100">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                <div>
                    <label class="block text-sm font-semibold text-slate-700 mb-2">No. Referensi / Bukti</label>
                    <input v-model="form.referensi" type="text" placeholder="Contoh: INV-001" class="w-full border border-slate-300 rounded-lg px-4 py-2.5 outline-none focus:border-blue-500">
                </div>
                <div>
                    <label class="block text-sm font-semibold text-slate-700 mb-2">Keterangan Transaksi</label>
                    <input v-model="form.keterangan" type="text" placeholder="Catatan jurnal..." class="w-full border border-slate-300 rounded-lg px-4 py-2.5 outline-none focus:border-blue-500">
                </div>
            </div>

            <table class="min-w-full border border-slate-200 rounded-lg overflow-hidden">
                <thead class="bg-slate-100">
                    <tr>
                        <th class="px-4 py-3 text-left text-xs font-bold text-slate-600 uppercase">Pilih Akun</th>
                        <th class="px-4 py-3 text-right text-xs font-bold text-slate-600 uppercase w-48">Debit (Rp)</th>
                        <th class="px-4 py-3 text-right text-xs font-bold text-slate-600 uppercase w-48">Kredit (Rp)</th>
                        <th class="px-4 py-3 text-center w-16"></th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-slate-100">
                    <tr v-for="(item, index) in form.items" :key="index">
                        <td class="p-2">
                            <select v-model="item.akun_id" class="w-full border border-slate-300 rounded-md px-3 py-2 outline-none focus:border-blue-500 text-sm">
                                <option value="" disabled>-- Pilih Akun --</option>
                                <option v-for="akun in akunList" :key="akun.id" :value="akun.id">
                                    {{ akun.kode }} - {{ akun.nama }}
                                </option>
                            </select>
                        </td>
                        <td class="p-2">
                            <input v-model.number="item.debit" type="number" min="0" class="w-full border border-slate-300 rounded-md px-3 py-2 text-right outline-none focus:border-blue-500 text-sm">
                        </td>
                        <td class="p-2">
                            <input v-model.number="item.kredit" type="number" min="0" class="w-full border border-slate-300 rounded-md px-3 py-2 text-right outline-none focus:border-blue-500 text-sm">
                        </td>
                        <td class="p-2 text-center">
                            <button @click="removeRow(index)" :disabled="form.items.length <= 2" class="text-red-500 hover:text-red-700 disabled:opacity-30">
                                <i class="pi pi-trash"></i>
                            </button>
                        </td>
                    </tr>
                </tbody>
            </table>

            <div class="mt-4 flex justify-between items-center">
                <button @click="addRow" class="text-sm font-bold text-blue-600 hover:text-blue-800">
                    <i class="pi pi-plus mr-1"></i> Tambah Baris Akun
                </button>
                <div class="flex gap-8 text-right bg-slate-50 p-4 rounded-lg border border-slate-200">
                    <div>
                        <p class="text-xs font-bold text-slate-500 mb-1">TOTAL DEBIT</p>
                        <p class="font-bold text-lg text-slate-800">Rp {{ totalDebit.toLocaleString('id-ID') }}</p>
                    </div>
                    <div>
                        <p class="text-xs font-bold text-slate-500 mb-1">TOTAL KREDIT</p>
                        <p class="font-bold text-lg text-slate-800">Rp {{ totalKredit.toLocaleString('id-ID') }}</p>
                    </div>
                </div>
            </div>

            <div class="mt-8 flex items-center justify-between">
                <div class="text-sm font-semibold">
                    <span v-if="isBalance" class="text-green-600"><i class="pi pi-check-circle mr-1"></i> Transaksi Balance</span>
                    <span v-else class="text-red-500"><i class="pi pi-times-circle mr-1"></i> Transaksi Belum Balance</span>
                </div>
                <button @click="submitJurnal" :disabled="!isBalance || isLoading"
                    class="bg-slate-900 text-white font-bold px-8 py-3 rounded-xl shadow-md hover:bg-slate-800 disabled:opacity-50 transition-all flex items-center">
                    <i v-if="isLoading" class="pi pi-spinner pi-spin mr-2"></i>
                    <span>{{ isLoading ? 'Menyimpan...' : 'Simpan Jurnal' }}</span>
                </button>
            </div>
        </div>
    </div>
</template>
