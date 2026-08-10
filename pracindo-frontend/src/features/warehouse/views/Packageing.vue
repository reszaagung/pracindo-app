<!--
   features/warehouse/views/Packageing.vue
   ===============================================
   Transfer Hasil Produksi & Pengemasan
   Desain seragam dengan ekosistem Gudang/Akuntansi (Responsive).
-->
<template>
    <div class="flex flex-col w-full animate-fade-in relative space-y-6">

        <!-- Header Halaman -->
        <div class="flex justify-between items-end">
            <div>
                <p class="text-xs text-slate-400 mb-1">
                    <span class="hover:text-slate-700 transition-colors">Warehouse</span> /
                    <span class="hover:text-slate-700 transition-colors font-semibold">Packaging & Hasil</span>
                </p>
                <h2 class="text-xl md:text-2xl font-bold text-slate-800 tracking-tight">Transfer Hasil Produksi</h2>
                <p class="text-xs md:text-sm text-slate-500 mt-1">Catat hasil akhir produk jadi atau varian ke gudang
                    penyimpanan.</p>
            </div>
        </div>

        <div class="bg-white border border-slate-200 rounded-[24px] p-4 md:p-6 shadow-sm w-full">
            <!-- Header Form (Informasi Produksi) -->
            <div class="mb-6 pb-6 border-b border-slate-100">
                <h3 class="text-sm font-bold text-slate-800 mb-4 flex items-center gap-2">
                    <i class="pi pi-info-circle text-emerald-600"></i> Informasi Produksi
                </h3>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div class="flex flex-col gap-2">
                        <label class="text-xs font-bold uppercase tracking-wider text-slate-500">No. Batch /
                            Sesi</label>
                        <input type="text" v-model="formHeader.batch_no" placeholder="Contoh: BATCH-2026-04"
                            class="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-slate-800 text-slate-800 font-medium transition-colors">
                    </div>
                    <div class="flex flex-col gap-2">
                        <label class="text-xs font-bold uppercase tracking-wider text-slate-500">Gudang Tujuan</label>
                        <div class="relative">
                            <select v-model="formHeader.gudang_tujuan"
                                class="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-slate-800 text-slate-800 font-medium appearance-none cursor-pointer transition-colors">
                                <option value="" disabled>-- Pilih Gudang --</option>
                                <option value="PT">Gudang PT (Utama)</option>
                                <option value="CV">Gudang CV (Cabang)</option>
                            </select>
                            <i
                                class="pi pi-chevron-down absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 text-xs pointer-events-none"></i>
                        </div>
                    </div>
                    <div class="flex flex-col gap-2">
                        <label class="text-xs font-bold uppercase tracking-wider text-slate-500">Tanggal Catat</label>
                        <input type="date" v-model="formHeader.tanggal"
                            class="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-slate-800 text-slate-800 font-medium transition-colors">
                    </div>
                </div>
            </div>

            <!-- Bagian Item Produk -->
            <div class="mb-6">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-sm font-bold text-slate-800 flex items-center gap-2">
                        <i class="pi pi-box text-blue-600"></i> Detail Item Produk
                    </h3>
                    <button @click="addRow"
                        class="px-3 py-1.5 md:px-4 md:py-2 bg-blue-50 hover:bg-blue-100 text-blue-700 text-[10px] md:text-xs font-bold rounded-lg transition-colors flex items-center gap-2">
                        <i class="pi pi-plus"></i> Tambah Baris
                    </button>
                </div>

                <!-- Tampilan Desktop (Tabel) -->
                <div class="hidden md:block overflow-x-auto custom-scrollbar">
                    <table class="w-full text-left text-sm table-fixed min-w-[50rem]">
                        <thead class="text-slate-500 bg-slate-50/50">
                            <tr>
                                <th class="py-3 px-3 font-semibold rounded-tl-xl w-[25%]">Varian / Nama Produk</th>
                                <th class="py-3 px-3 font-semibold w-[20%]">Jenis Kemasan</th>
                                <th class="py-3 px-3 font-semibold w-[15%] text-right">Berat/Unit (Kg)</th>
                                <th class="py-3 px-3 font-semibold w-[15%] text-right">Jml Koli/Unit</th>
                                <th class="py-3 px-3 font-semibold w-[15%] text-right">Total Berat</th>
                                <th class="py-3 px-3 font-semibold w-[10%] text-center rounded-tr-xl">Aksi</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-100">
                            <tr v-for="(item, index) in formItems" :key="index"
                                class="hover:bg-slate-50/30 transition-colors">
                                <td class="py-2 px-2 align-top">
                                    <input type="text" v-model="item.nama_produk" placeholder="Misal: Super White SC SC"
                                        class="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-800 font-medium focus:outline-none focus:ring-2 focus:ring-slate-800 transition-colors">
                                </td>
                                <td class="py-2 px-2 align-top">
                                    <input type="text" v-model="item.packaging" placeholder="Contoh: Karung / Sak"
                                        class="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-800 transition-colors">
                                </td>
                                <td class="py-2 px-2 align-top">
                                    <input type="number" v-model.number="item.unit_kg" @input="calcWeight(index)"
                                        min="0" step="0.01"
                                        class="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm text-right text-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-800 transition-colors">
                                </td>
                                <td class="py-2 px-2 align-top">
                                    <input type="number" v-model.number="item.total_unit" @input="calcWeight(index)"
                                        min="0"
                                        class="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm text-right text-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-800 transition-colors">
                                </td>
                                <td class="py-2 px-2 align-top">
                                    <input type="number" v-model.number="item.berat" readonly
                                        class="w-full bg-slate-100 border border-slate-200 rounded-lg px-3 py-2 text-sm text-right font-bold text-slate-600 cursor-not-allowed">
                                </td>
                                <td class="py-2 px-2 align-top text-center pt-3">
                                    <button @click="removeRow(index)"
                                        class="w-8 h-8 bg-rose-50 text-rose-500 rounded-lg hover:bg-rose-500 hover:text-white transition-colors flex items-center justify-center mx-auto"
                                        title="Hapus Baris">
                                        <i class="pi pi-trash text-xs"></i>
                                    </button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <!-- Tampilan Mobile (Card) -->
                <div class="md:hidden flex flex-col gap-4">
                    <div v-for="(item, index) in formItems" :key="'mob-' + index"
                        class="border border-slate-200 rounded-xl p-4 bg-slate-50/30">
                        <div class="flex justify-between items-center mb-4 border-b border-slate-100 pb-2">
                            <span class="font-bold text-slate-600 text-xs uppercase tracking-wider">Item #{{ index + 1
                                }}</span>
                            <button @click="removeRow(index)"
                                class="text-rose-500 bg-rose-50 p-1.5 rounded-lg hover:bg-rose-100">
                                <i class="pi pi-trash text-[10px]"></i>
                            </button>
                        </div>
                        <div class="flex flex-col gap-3">
                            <div class="flex flex-col gap-1.5">
                                <label class="text-[10px] font-bold text-slate-500 uppercase">Varian / Nama
                                    Produk</label>
                                <input type="text" v-model="item.nama_produk" placeholder="Misal: Super White SC SC"
                                    class="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-800 font-medium focus:outline-none focus:ring-2 focus:ring-slate-800">
                            </div>
                            <div class="flex flex-col gap-1.5">
                                <label class="text-[10px] font-bold text-slate-500 uppercase">Jenis Kemasan</label>
                                <input type="text" v-model="item.packaging" placeholder="Contoh: Karung / Sak"
                                    class="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-800">
                            </div>
                            <div class="grid grid-cols-2 gap-3">
                                <div class="flex flex-col gap-1.5">
                                    <label class="text-[10px] font-bold text-slate-500 uppercase">Berat/Unit
                                        (Kg)</label>
                                    <input type="number" v-model.number="item.unit_kg" @input="calcWeight(index)"
                                        min="0" step="0.01"
                                        class="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-sm text-right text-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-800">
                                </div>
                                <div class="flex flex-col gap-1.5">
                                    <label class="text-[10px] font-bold text-slate-500 uppercase">Jml Koli/Unit</label>
                                    <input type="number" v-model.number="item.total_unit" @input="calcWeight(index)"
                                        min="0"
                                        class="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-sm text-right text-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-800">
                                </div>
                            </div>
                            <div
                                class="flex justify-between items-center bg-slate-100 p-2.5 rounded-lg mt-1 border border-slate-200">
                                <span class="text-[10px] font-bold text-slate-500 uppercase">Total Berat (Kg):</span>
                                <span class="font-black text-slate-800">{{ item.berat || '0' }}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Kontrol Bawah & Tombol Simpan -->
            <div class="flex flex-col sm:flex-row justify-end items-center gap-3 pt-4 border-t border-slate-100">
                <button @click="resetForm"
                    class="w-full sm:w-auto px-6 py-3 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 font-bold text-sm rounded-xl transition-colors text-center">
                    Reset Form
                </button>
                <button @click="saveData" :disabled="isSaving"
                    class="w-full sm:w-auto px-8 py-3 bg-slate-900 hover:bg-slate-800 text-white font-bold text-sm rounded-xl shadow-md transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed transform hover:-translate-y-0.5">
                    <i v-if="isSaving" class="pi pi-spin pi-spinner text-xs"></i>
                    <i v-else class="pi pi-save text-xs"></i>
                    <span>{{ isSaving ? 'Menyimpan...' : 'Simpan Hasil Produksi' }}</span>
                </button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import api from '@/utils/api'

const isSaving = ref(false)

const formHeader = reactive({
    batch_no: '',
    gudang_tujuan: 'PT',
    tanggal: new Date().toISOString().split('T')[0]
})

const formItems = ref([
    { nama_produk: '', packaging: '', unit_kg: 0, total_unit: 0, berat: 0 }
])

const calcWeight = (index) => {
    const item = formItems.value[index]
    item.berat = (parseFloat(item.unit_kg) * parseFloat(item.total_unit)) || 0
}

const addRow = () => {
    formItems.value.push({ nama_produk: '', packaging: '', unit_kg: 0, total_unit: 0, berat: 0 })
}

const removeRow = (index) => {
    if (formItems.value.length > 1) {
        formItems.value.splice(index, 1)
    } else {
        alert("Minimal harus ada 1 item produk!")
    }
}

const resetForm = () => {
    formHeader.batch_no = ''
    formHeader.gudang_tujuan = 'PT'
    formHeader.tanggal = new Date().toISOString().split('T')[0]
    formItems.value = [{ nama_produk: '', packaging: '', unit_kg: 0, total_unit: 0, berat: 0 }]
}

const saveData = async () => {
    if (!formHeader.batch_no) return alert("Nomor Batch / Sesi Produksi wajib diisi!")

    isSaving.value = true
    try {
        const payload = {
            header: formHeader,
            items: formItems.value
        }

        const response = await api.post('warehouse/packaging-hasil-produksi/', payload)

        if (response.status === 200 || response.status === 201) {
            alert("Transfer Hasil Produksi Berhasil Disimpan!")
            resetForm()
        }
    } catch (error) {
        console.error("Gagal menyimpan packaging:", error)
        alert("Gagal menyimpan data ke server.")
    } finally {
        isSaving.value = false
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

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background: #94a3b8;
}
</style>