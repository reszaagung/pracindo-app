<template>
    <div class="flex flex-col w-full animate-fade-in relative">
        <!-- Header -->
        <div class="mb-4 md:mb-6 flex flex-col md:flex-row justify-between items-start md:items-end gap-4 md:gap-0">
            <div>
                <p class="text-xs text-slate-400 mb-1">
                    <router-link to="/" class="hover:text-slate-700 transition-colors">Dashboard</router-link> ›
                    <router-link to="/warehouse/do"
                        class="hover:text-slate-700 transition-colors">Logistik</router-link> › Buat Surat Jalan
                </p>
                <div class="flex items-center gap-3">
                    <h2 class="text-xl md:text-2xl font-bold text-slate-800 tracking-tight">Surat Jalan (Delivery Order)
                    </h2>
                    <span
                        class="bg-amber-100 text-amber-700 text-[10px] font-bold px-2.5 py-1 rounded-full tracking-wide">PENGIRIMAN</span>
                </div>
            </div>

            <div class="flex items-center gap-2">
                <button type="button" @click="resetForm"
                    class="px-4 py-2 bg-white border border-slate-200 hover:bg-slate-50 text-slate-600 text-xs font-bold rounded-lg transition-colors flex items-center gap-2 shadow-sm">
                    <i class="pi pi-refresh"></i> Reset Form
                </button>
            </div>
        </div>

        <form @submit.prevent="terbitkanSuratJalan"
            class="bg-white border border-slate-200 rounded-[24px] p-4 md:p-8 shadow-[0_4px_20px_rgba(0,0,0,0.02)] w-full">

            <!-- Informasi Pengiriman -->
            <div class="grid grid-cols-1 md:grid-cols-4 gap-4 md:gap-6 mb-8 border-b border-slate-100 pb-8">
                <div class="flex flex-col gap-2">
                    <label class="text-xs md:text-sm font-bold text-slate-700">Tanggal Pengiriman</label>
                    <input v-model="draf.tanggal" type="date" required
                        class="px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-amber-500 text-sm text-slate-800" />
                </div>
                <div class="flex flex-col gap-2">
                    <label class="text-xs md:text-sm font-bold text-slate-700">Referensi SO (Opsional)</label>
                    <input v-model="draf.referensi_so" type="text" placeholder="Contoh: SO-2608-0001"
                        class="px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-amber-500 text-sm text-slate-800" />
                </div>
                <div class="flex flex-col gap-2">
                    <label class="text-xs md:text-sm font-bold text-slate-700">Nama Pengemudi</label>
                    <input v-model="draf.pengemudi" type="text" placeholder="Nama Supir..." required
                        class="px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-amber-500 text-sm text-slate-800" />
                </div>
                <div class="flex flex-col gap-2">
                    <label class="text-xs md:text-sm font-bold text-slate-700">Plat Nomor Kendaraan</label>
                    <input v-model="draf.plat_nomor" type="text" placeholder="B 1234 CD" required
                        class="px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-amber-500 text-sm text-slate-800 uppercase" />
                </div>
            </div>

            <!-- Detail Barang yang Dikirim -->
            <div class="w-full mb-8">
                <div class="flex justify-between items-center mb-4 pb-2 mt-2">
                    <h3 class="text-sm md:text-base font-bold text-slate-800">Daftar Barang (Item Packing)</h3>
                </div>

                <table class="w-full text-left text-sm table-fixed border-collapse">
                    <thead class="hidden md:table-header-group text-slate-500 bg-slate-50/50 border-b border-slate-200">
                        <tr>
                            <th class="py-3 px-3 font-semibold rounded-tl-xl w-[5%] text-center">No</th>
                            <th class="py-3 px-3 font-semibold w-[40%]">Nama Barang / Deskripsi</th>
                            <th class="py-3 px-2 font-semibold w-[15%] text-right">Qty Kirim</th>
                            <th class="py-3 px-2 font-semibold w-[15%]">Satuan</th>
                            <th class="py-3 px-2 font-semibold rounded-tr-xl w-[25%]">Keterangan (Kondisi)</th>
                        </tr>
                    </thead>
                    <tbody class="block md:table-row-group">
                        <tr v-for="(item, index) in draf.items" :key="index"
                            class="block md:table-row bg-white border border-slate-200 md:border-b md:border-x-0 md:border-t-0 md:border-slate-100 rounded-2xl md:rounded-none mb-6 md:mb-0 p-4 md:p-0">

                            <td class="hidden md:table-cell py-3 px-3 text-center text-slate-400 font-bold">
                                {{ index + 1 }}
                            </td>

                            <td class="block md:table-cell md:py-3 md:px-2 mb-3 md:mb-0">
                                <label class="md:hidden text-xs font-bold text-slate-500 mb-1 block">Barang #{{ index +
                                    1 }}</label>
                                <input v-model="item.nama_barang" type="text" placeholder="Masukkan nama barang..."
                                    class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-amber-500 text-slate-800" />
                            </td>

                            <td class="block md:table-cell md:py-3 md:px-2 mb-3 md:mb-0">
                                <label class="md:hidden text-xs font-bold text-slate-500 mb-1 block">Qty</label>
                                <input v-model.number="item.qty" type="number" min="0" step="0.01"
                                    class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm md:text-right focus:ring-2 focus:ring-amber-500 text-slate-800"
                                    placeholder="0" />
                            </td>

                            <td class="block md:table-cell md:py-3 md:px-2 mb-3 md:mb-0">
                                <label class="md:hidden text-xs font-bold text-slate-500 mb-1 block">Satuan</label>
                                <select v-model="item.satuan"
                                    class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-amber-500 text-slate-800">
                                    <option value="Pcs">Pcs</option>
                                    <option value="Kg">Kg</option>
                                    <option value="Box">Box</option>
                                    <option value="Palet">Palet</option>
                                    <option value="Roll">Roll</option>
                                </select>
                            </td>

                            <td class="block md:table-cell md:py-3 md:px-2 mb-3 md:mb-0">
                                <label class="md:hidden text-xs font-bold text-slate-500 mb-1 block">Keterangan</label>
                                <input v-model="item.keterangan" type="text" placeholder="Baik / Rusak / Dll..."
                                    class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-amber-500 text-slate-800" />
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <div class="flex flex-col md:flex-row justify-between items-start gap-6 mt-4">
                <div class="w-full md:w-1/2">
                    <label class="text-xs font-bold text-slate-700 block mb-2">Instruksi Khusus / Catatan Gudang</label>
                    <textarea v-model="draf.catatan" rows="3"
                        placeholder="Instruksi jalan, alamat tujuan, atau handling khusus..."
                        class="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 resize-none text-slate-800"></textarea>
                </div>

                <div class="w-full md:w-1/3 pt-6">
                    <button type="submit" :disabled="sedangProses"
                        class="w-full justify-center px-6 py-3.5 bg-amber-500 hover:bg-amber-600 disabled:bg-slate-400 text-white font-bold rounded-xl shadow-[0_4px_15px_rgba(245,158,11,0.3)] transition-all flex items-center gap-2 cursor-pointer disabled:cursor-not-allowed">
                        <i class="pi" :class="sedangProses ? 'pi-spin pi-spinner' : 'pi-send'"></i>
                        {{ sedangProses ? 'Mencetak...' : 'Terbitkan & Cetak Surat Jalan' }}
                    </button>
                </div>
            </div>
        </form>
    </div>
</template>

<script setup>
import { reactive } from 'vue'
import { useDeliveryOrder } from '@/features/warehouse/composables/useDeliveryOrder'

// Panggil composable yang baru saja dibuat
const { sedangProses, pesanError, simpanDO } = useDeliveryOrder()

const hariIni = () => {
    const t = new Date(Date.now() - new Date().getTimezoneOffset() * 60_000)
    return t.toISOString().slice(0, 10)
}

const itemKosong = () => ({ nama_barang: '', qty: null, satuan: 'Pcs', keterangan: '' })

// Sesuai permintaan Anda sebelumnya: Langsung sediakan 8 baris item!
const draf = reactive({
    tanggal: hariIni(),
    referensi_so: '',
    pengemudi: '',
    plat_nomor: '',
    catatan: '',
    items: Array(8).fill().map(() => itemKosong())
})

const resetForm = () => {
    draf.tanggal = hariIni()
    draf.referensi_so = ''
    draf.pengemudi = ''
    draf.plat_nomor = ''
    draf.catatan = ''
    draf.items = Array(8).fill().map(() => itemKosong())
}

const terbitkanSuratJalan = async () => {
    const itemValid = draf.items.filter(item => item.nama_barang.trim() !== '' && item.qty > 0)

    if (itemValid.length === 0) {
        alert("Peringatan: Isi minimal 1 barang beserta Qty-nya sebelum menerbitkan Surat Jalan.")
        return
    }

    const payload = {
        tanggal: draf.tanggal,
        referensi_so: draf.referensi_so,
        pengemudi: draf.pengemudi,
        plat_nomor: draf.plat_nomor,
        catatan: draf.catatan,
        items: itemValid
    }

    const hasil = await simpanDO(payload)

    if (hasil.success) {
        alert("Surat Jalan berhasil diterbitkan!")
        resetForm()
    } else {
        alert(pesanError.value || "Gagal menerbitkan Surat Jalan.")
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