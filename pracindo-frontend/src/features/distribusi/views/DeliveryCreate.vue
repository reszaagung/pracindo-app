<template>
    <div class="flex flex-col w-full animate-fade-in relative">
        <div class="mb-6 flex items-center gap-4">
            <button @click="$router.push('/distribusi')" class="w-10 h-10 bg-white border border-slate-200 rounded-xl flex items-center justify-center hover:bg-slate-50 transition-colors shadow-sm">
                <i class="pi pi-arrow-left text-slate-600 text-sm"></i>
            </button>
            <div>
                <h1 class="text-xl md:text-2xl font-bold text-slate-800 tracking-tight">Rakit Pengiriman Baru</h1>
                <p class="text-xs md:text-sm text-slate-500 mt-1">Pilih barang dari gudang dan tugaskan armada.</p>
            </div>
        </div>

        <div v-if="galat" class="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-600 font-medium flex items-start gap-3 shadow-sm">
            <i class="pi pi-exclamation-triangle mt-0.5"></i>
            <span>{{ galat }}</span>
        </div>

        <form @submit.prevent="simpanPengiriman" class="flex flex-col gap-6 pb-20">
            <div class="bg-white border border-slate-200 rounded-[24px] p-6 shadow-sm w-full">
                <h2 class="text-sm font-bold text-slate-800 mb-4 pb-2 border-b border-slate-100">Informasi Armada & Kurir</h2>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
                    <div class="flex flex-col gap-1.5">
                        <label class="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Tanggal Pengiriman</label>
                        <input type="date" v-model="form.tanggal" required
                            class="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-800 font-medium" />
                    </div>

                    <div class="flex flex-col gap-1.5">
                        <label class="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Pilih Armada (Truk)</label>
                        <select v-model="form.kendaraan_id" required
                            class="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-800 font-medium">
                            <option value="" disabled>-- Pilih Armada Tersedia --</option>
                            <option v-for="armada in daftarArmada" :key="armada.id" :value="armada.id">
                                {{ armada.plat_nomor }} - {{ armada.nama }}
                            </option>
                        </select>
                    </div>

                    <div class="flex flex-col gap-1.5">
                        <label class="text-[10px] font-bold text-slate-500 uppercase tracking-wider">ID Kurir Bertugas</label>
                        <input type="number" v-model="form.kurir_id" required placeholder="Masukkan ID User Kurir..."
                            class="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-800 font-medium" />
                    </div>

                    <div class="flex flex-col gap-1.5">
                        <label class="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Entitas Perusahaan</label>
                        <input type="number" v-model="form.entitas_id" required placeholder="ID Entitas Perusahaan..."
                            class="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-800 font-medium" />
                    </div>

                    <div class="flex flex-col gap-1.5 md:col-span-2">
                        <label class="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Catatan Tambahan</label>
                        <input type="text" v-model="form.catatan" placeholder="Instruksi khusus untuk kurir..."
                            class="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-800 font-medium" />
                    </div>
                </div>
            </div>

            <div class="bg-white border border-slate-200 rounded-[24px] p-6 shadow-sm w-full">
                <div class="flex justify-between items-center mb-4 pb-2 border-b border-slate-100">
                    <h2 class="text-sm font-bold text-slate-800">Muatan Barang (Pilih dari Warehouse)</h2>
                    <span class="px-3 py-1 bg-blue-50 text-blue-600 rounded-lg text-xs font-bold">
                        {{ form.distribusi_ids.length }} Dipilih
                    </span>
                </div>

                <div v-if="sedangMemuatBarang" class="py-8 flex justify-center">
                    <i class="pi pi-spin pi-spinner text-2xl text-blue-500"></i>
                </div>

                <div v-else-if="barangTersedia.length > 0" class="flex flex-col gap-3">
                    <label v-for="barang in barangTersedia" :key="barang.id"
                        class="flex items-start gap-4 p-4 border rounded-xl cursor-pointer transition-colors"
                        :class="form.distribusi_ids.includes(barang.id) ? 'border-blue-500 bg-blue-50/30' : 'border-slate-200 bg-slate-50 hover:bg-slate-100'">
                        <input type="checkbox" :value="barang.id" v-model="form.distribusi_ids" class="mt-1 w-4 h-4 text-blue-600 rounded border-slate-300 focus:ring-blue-500">
                        <div class="flex-1">
                            <div class="flex justify-between">
                                <span class="font-bold text-slate-800">{{ barang.pelanggan_nama }}</span>
                                <span class="text-xs font-black text-slate-500">{{ barang.nomor }}</span>
                            </div>
                            <p class="text-xs text-slate-500 mt-1"><i class="pi pi-map-marker text-[10px]"></i> {{ barang.alamat }}</p>
                        </div>
                    </label>
                </div>

                <div v-else class="py-8 text-center">
                    <i class="pi pi-check-circle text-3xl text-emerald-500 mb-2"></i>
                    <p class="text-sm font-bold text-slate-800">Gudang Kosong</p>
                    <p class="text-xs text-slate-500 mt-1">Tidak ada barang yang menunggu pengiriman.</p>
                </div>
            </div>

            <div class="fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 p-4 px-6 shadow-[0_-4px_20px_rgba(0,0,0,0.05)] z-40 lg:left-[88px]">
                <div class="max-w-7xl mx-auto flex justify-end gap-4">
                    <button type="button" @click="$router.push('/distribusi')" class="px-6 py-3 bg-slate-100 hover:bg-slate-200 text-slate-700 text-sm font-bold rounded-xl transition-colors">
                        Batal
                    </button>
                    <button type="submit" :disabled="sedangProses || form.distribusi_ids.length === 0"
                        class="px-8 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 text-white text-sm font-bold rounded-xl shadow-md transition-all flex items-center gap-2">
                        <i v-if="sedangProses" class="pi pi-spin pi-spinner text-xs"></i>
                        <i v-else class="pi pi-save text-xs"></i>
                        <span>Simpan & Rakit Jadwal</span>
                    </button>
                </div>
            </div>
        </form>
    </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { apiDistribusi } from '../api'

const router = useRouter()
const daftarArmada = ref([])
const barangTersedia = ref([])
const sedangMemuatBarang = ref(false)
const sedangProses = ref(false)
const galat = ref('')

const form = reactive({
    entitas_id: 1,
    kurir_id: '',
    kendaraan_id: '',
    tanggal: new Date().toISOString().split('T')[0],
    catatan: '',
    distribusi_ids: []
})

const muatDataAwal = async () => {
    sedangMemuatBarang.value = true
    try {
        const [resArmada, resBarang] = await Promise.all([
            apiDistribusi.getArmada(),
            apiDistribusi.getDistribusiTersedia()
        ])
        daftarArmada.value = resArmada.results || resArmada || []
        barangTersedia.value = resBarang || []
    } catch (err) {
        galat.value = 'Gagal memuat data pendukung dari server.'
    } finally {
        sedangMemuatBarang.value = false
    }
}

const simpanPengiriman = async () => {
    sedangProses.value = true
    galat.value = ''
    try {
        await apiDistribusi.rakitPengiriman(form)
        router.push('/distribusi')
    } catch (err) {
        galat.value = err.response?.data?.detail || 'Gagal menyimpan pengiriman.'
    } finally {
        sedangProses.value = false
    }
}

onMounted(() => {
    muatDataAwal()
})
</script>

<style scoped>
.animate-fade-in { animation: fadeIn 0.3s ease-out forwards; }
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
</style>
