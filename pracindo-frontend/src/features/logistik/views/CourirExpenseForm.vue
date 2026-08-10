<!--
  src/features/logistik/views/CourierExpenseForm.vue
  Form Lapor Pengeluaran Khusus Kurir Lapangan
-->
<template>
    <div class="min-h-screen bg-slate-50 font-sans text-slate-800 flex flex-col">

        <!-- Header -->
        <header
            class="bg-white border-b border-slate-200 px-4 py-4 flex items-center justify-between sticky top-0 z-30 shadow-sm">
            <button @click="$router.push('/kurir')"
                class="w-10 h-10 bg-slate-100 rounded-full flex items-center justify-center text-slate-600 active:bg-slate-200 transition-colors">
                <i class="pi pi-arrow-left"></i>
            </button>
            <h1 class="font-black text-lg text-slate-800">Lapor Pengeluaran</h1>
            <div class="w-10 h-10"></div> <!-- Spacer -->
        </header>

        <!-- Form Area -->
        <main class="flex-1 p-6 relative">

            <div class="bg-white rounded-[24px] border border-slate-200 shadow-sm p-6 mb-6">
                <!-- Kategori Pengeluaran -->
                <div class="mb-6">
                    <label class="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Jenis
                        Pengeluaran</label>
                    <div class="grid grid-cols-2 gap-3">
                        <button v-for="kat in kategori" :key="kat.id" @click="form.kategori = kat.id"
                            class="py-3 px-2 rounded-xl border-2 font-bold text-sm transition-all flex flex-col items-center gap-2"
                            :class="form.kategori === kat.id ? 'border-amber-500 bg-amber-50 text-amber-700' : 'border-slate-100 bg-white text-slate-500'">
                            <i :class="['pi', kat.ikon, 'text-xl']"></i>
                            {{ kat.label }}
                        </button>
                    </div>
                </div>

                <!-- Nominal Angka -->
                <div class="mb-6">
                    <label class="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Total Biaya
                        (Rp)</label>
                    <div class="relative">
                        <span class="absolute left-4 top-1/2 -translate-y-1/2 font-black text-slate-400">Rp</span>
                        <input type="number" v-model="form.nominal" placeholder="0"
                            class="w-full pl-12 pr-4 py-4 bg-slate-50 border border-slate-200 rounded-xl text-xl font-black focus:outline-none focus:ring-2 focus:ring-amber-500 text-slate-800 transition-colors" />
                    </div>
                </div>

                <!-- Keterangan / Catatan -->
                <div class="mb-6">
                    <label class="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Catatan
                        Tambahan</label>
                    <textarea v-model="form.catatan" rows="2" placeholder="Misal: Tambal ban bocor di tol km 14..."
                        class="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-amber-500 text-slate-800 transition-colors resize-none"></textarea>
                </div>

                <!-- Upload Foto Bukti -->
                <div>
                    <label class="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Foto Struk /
                        Bon</label>

                    <!-- Area Upload -->
                    <div v-if="!fotoPreview" class="relative">
                        <input type="file" accept="image/*" capture="environment" @change="handleFotoUpload"
                            class="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10" />
                        <div
                            class="w-full h-32 bg-slate-50 border-2 border-dashed border-slate-300 rounded-xl flex flex-col items-center justify-center text-slate-500">
                            <i class="pi pi-camera text-3xl mb-2 text-slate-400"></i>
                            <span class="text-sm font-bold">Buka Kamera / Pilih Foto</span>
                        </div>
                    </div>

                    <!-- Preview Foto -->
                    <div v-else
                        class="relative w-full h-48 rounded-xl border border-slate-200 overflow-hidden bg-slate-900 group">
                        <img :src="fotoPreview" class="w-full h-full object-cover opacity-90" />
                        <button @click="hapusFoto"
                            class="absolute top-3 right-3 w-10 h-10 bg-rose-500 rounded-full flex items-center justify-center text-white shadow-md active:scale-95 transition-transform">
                            <i class="pi pi-trash"></i>
                        </button>
                    </div>
                </div>
            </div>

            <!-- Tombol Kirim -->
            <button @click="kirimPengeluaran" :disabled="!formBisaDikirim"
                class="w-full py-4 rounded-xl font-black text-lg transition-all shadow-md flex items-center justify-center gap-3 disabled:opacity-50"
                :class="formBisaDikirim ? 'bg-slate-900 text-white active:scale-95' : 'bg-slate-300 text-slate-500 cursor-not-allowed'">
                <i class="pi pi-cloud-upload"></i>
                Kirim ke Akuntansi
            </button>

        </main>
    </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const kategori = [
    { id: 'BENSIN', label: 'Bahan Bakar', ikon: 'pi-car' },
    { id: 'TOL', label: 'Tarif Tol', ikon: 'pi-ticket' },
    { id: 'MAINTENANCE', label: 'Perbaikan', ikon: 'pi-wrench' },
    { id: 'LAINNYA', label: 'Lainnya', ikon: 'pi-wallet' }
]

const form = ref({
    kategori: '',
    nominal: '',
    catatan: ''
})

const fotoPreview = ref(null)
const fotoFile = ref(null)

const handleFotoUpload = (event) => {
    const file = event.target.files[0]
    if (!file) return

    fotoFile.value = file
    // Buat URL sementara untuk menampilkan preview gambar
    fotoPreview.value = URL.createObjectURL(file)
}

const hapusFoto = () => {
    fotoFile.value = null
    fotoPreview.value = null
}

// Validasi sederhana: Kategori, Nominal, dan Foto harus ada
const formBisaDikirim = computed(() => {
    return form.value.kategori !== '' &&
        form.value.nominal > 0 &&
        fotoFile.value !== null
})

const kirimPengeluaran = async () => {
    if (!formBisaDikirim.value) return

    alert('Data berhasil diantrekan! Tim Akuntansi akan mereview pengajuan ini.')

}
</script>