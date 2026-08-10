<!-- src/features/kurir/views/CourierTaskDetail.vue -->
<template>
    <div class="min-h-screen bg-slate-50 max-w-md mx-auto flex flex-col font-sans relative shadow-2xl">

        <!-- HEADER BIRU -->
        <div
            class="bg-[#5C6BC0] px-6 pt-10 pb-6 shrink-0 flex items-center justify-between text-white rounded-b-3xl shadow-md relative z-20">
            <div class="flex items-center gap-4">
                <button @click="kembali"
                    class="w-10 h-10 rounded-full bg-white/25 hover:bg-white/35 flex items-center justify-center backdrop-blur-sm transition-colors active:scale-95">
                    <i class="pi pi-arrow-left"></i>
                </button>
                <div>
                    <h1 class="text-lg font-bold tracking-wide">{{ detailPengiriman?.nomor || 'Muatan Pengiriman' }}
                    </h1>
                    <p class="text-xs text-indigo-100 mt-0.5">Kelola titik perhentian & bukti terima</p>
                </div>
            </div>
        </div>

        <!-- KONTEN UTAMA -->
        <div class="flex-1 px-5 pt-6 pb-24 overflow-y-auto custom-scrollbar relative z-10">

            <div v-if="isLoading" class="flex flex-col items-center justify-center py-10 space-y-3">
                <i class="pi pi-spin pi-spinner text-3xl text-[#FF8A65]"></i>
                <p class="text-sm font-medium text-slate-500">Memuat titik perhentian...</p>
            </div>

            <div v-else>
                <!-- Info Status Perjalanan -->
                <div
                    class="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm mb-5 flex justify-between items-center">
                    <div>
                        <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-0.5">Status
                            Pengiriman</span>
                        <span class="text-xs font-black px-2.5 py-1 rounded-md uppercase border"
                            :class="getBadgeStatus(detailPengiriman?.status)">
                            {{ detailPengiriman?.status_label || detailPengiriman?.status }}
                        </span>
                    </div>
                    <div class="text-right">
                        <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-0.5">Total
                            Jarak</span>
                        <span class="text-sm font-black text-slate-700">{{ detailPengiriman?.jarak_total_km || '0' }}
                            km</span>
                    </div>
                </div>

                <!-- Daftar Titik Perhentian (Stops) -->
                <h3 class="text-xs font-black text-slate-400 uppercase tracking-wider mb-3 px-1">Daftar Titik Tujuan
                </h3>

                <div class="flex flex-col gap-4">
                    <div v-for="(stop, index) in detailPengiriman?.perhentian" :key="stop.id"
                        class="bg-white border border-slate-200 rounded-[20px] p-5 shadow-sm relative overflow-hidden">

                        <!-- Nomor Urut Badge -->
                        <div class="flex justify-between items-start mb-3 border-b border-slate-100 pb-3">
                            <div class="flex items-center gap-2">
                                <span
                                    class="w-6 h-6 rounded-full bg-indigo-50 text-[#5C6BC0] font-black text-xs flex items-center justify-center border border-indigo-100">
                                    {{ index + 1 }}
                                </span>
                                <span class="text-xs font-bold text-slate-500">{{ stop.nomor_distribusi }}</span>
                            </div>
                            <span class="px-2 py-0.5 rounded text-[9px] font-black tracking-widest uppercase border"
                                :class="getBadgeStopStatus(stop.status)">
                                {{ stop.status_label || stop.status }}
                            </span>
                        </div>

                        <!-- Info Toko / Pelanggan -->
                        <div class="mb-4">
                            <h2 class="text-sm font-black text-slate-800 mb-1">{{ stop.pelanggan_nama }}</h2>
                            <p class="text-xs text-slate-500 leading-relaxed"><i
                                    class="pi pi-map-marker text-rose-500 mr-1"></i> {{ stop.alamat }}</p>
                        </div>

                        <!-- Aksi Per Titik (Hanya aktif jika status pengiriman Berangkat) -->
                        <div class="flex flex-col gap-2 pt-2 border-t border-slate-100">
                            <!-- Jika belum sampai -->
                            <button v-if="stop.status === 'MENUNGGU'" @click="tandaiSampai(stop.id)"
                                class="w-full py-2.5 bg-amber-500 hover:bg-amber-600 text-white text-xs font-bold rounded-xl shadow-sm transition-colors flex items-center justify-center gap-1.5">
                                <i class="pi pi-map-marker text-[10px]"></i> Tiba di Lokasi Toko
                            </button>

                            <!-- Jika sudah sampai / ingin upload bukti -->
                            <button v-if="stop.status === 'SAMPAI' || stop.status === 'MENUNGGU'"
                                @click="bukaModalBukti(stop)"
                                class="w-full py-2.5 bg-[#5C6BC0] hover:bg-indigo-600 text-white text-xs font-bold rounded-xl shadow-sm transition-colors flex items-center justify-center gap-1.5">
                                <i class="pi pi-camera text-[10px]"></i> Upload Bukti Terima (POD)
                            </button>

                            <!-- Jika sudah tuntas -->
                            <div v-if="stop.status === 'DITERIMA'"
                                class="py-2 bg-emerald-50 text-emerald-600 text-xs font-bold rounded-xl flex items-center justify-center gap-1.5 border border-emerald-100">
                                <i class="pi pi-check-circle text-emerald-500"></i> Barang Berhasil Diterima
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- MODAL UPLOAD BUKTI TERIMA (POD) -->
        <div v-if="modalBuktiAktif"
            class="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-slate-900/60 backdrop-blur-sm sm:p-4 animate-fade-in">
            <div
                class="bg-white w-full max-w-md sm:rounded-[24px] rounded-t-[24px] shadow-2xl flex flex-col overflow-hidden max-h-[90vh]">

                <div class="px-5 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
                    <h3 class="text-sm font-bold text-slate-800">Unggah Bukti Terima (POD)</h3>
                    <button @click="modalBuktiAktif = false"
                        class="w-8 h-8 rounded-full bg-slate-200/60 text-slate-600 flex items-center justify-center">
                        <i class="pi pi-times"></i>
                    </button>
                </div>

                <div class="p-5 overflow-y-auto space-y-4">
                    <div>
                        <p class="text-xs font-bold text-slate-700 mb-1">{{ titikTerpilih?.pelanggan_nama }}</p>
                        <p class="text-[11px] text-slate-400">{{ titikTerpilih?.alamat }}</p>
                    </div>

                    <!-- Input Foto -->
                    <div class="flex flex-col gap-1.5">
                        <label class="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Foto Surat Jalan /
                            Barang di Lokasi</label>
                        <label
                            class="w-full h-36 border-2 border-dashed border-slate-300 rounded-xl bg-slate-50 flex flex-col items-center justify-center cursor-pointer hover:bg-slate-100 hover:border-[#5C6BC0] transition-colors group">
                            <i class="pi pi-camera text-2xl text-slate-400 group-hover:text-[#5C6BC0] mb-2"></i>
                            <span class="text-xs font-bold text-slate-500 group-hover:text-[#5C6BC0]">Ambil / Pilih
                                Foto</span>
                            <input type="file" accept="image/*" class="hidden" @change="handleFilePilih" />
                        </label>
                        <p v-if="formBukti.foto" class="text-xs text-emerald-600 font-bold mt-1 text-center"><i
                                class="pi pi-check-circle"></i> Berkas foto siap diunggah</p>
                    </div>

                    <!-- Catatan Opsional -->
                    <div class="flex flex-col gap-1.5">
                        <label class="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Catatan Tambahan
                            (Opsional)</label>
                        <textarea v-model="formBukti.catatan" placeholder="Contoh: Diterima oleh staf toko..."
                            class="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#5C6BC0] text-slate-800 font-medium h-20 resize-none"></textarea>
                    </div>
                </div>

                <div class="p-5 border-t border-slate-100 bg-white">
                    <button @click="kirimBuktiTerima" :disabled="!formBukti.foto || isUploading"
                        class="w-full py-3.5 bg-[#5C6BC0] hover:bg-indigo-600 text-white text-sm font-bold rounded-xl shadow-md transition-colors flex justify-center items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed">
                        <i v-if="isUploading" class="pi pi-spin pi-spinner"></i>
                        <i v-else class="pi pi-cloud-upload"></i>
                        <span>Kirim Bukti Terima</span>
                    </button>
                </div>
            </div>
        </div>

    </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/utils/api'

const route = useRoute()
const router = useRouter()
const pengirimanId = route.params.id

const isLoading = ref(true)
const detailPengiriman = ref(null)

// State Modal Bukti
const modalBuktiAktif = ref(false)
const titikTerpilih = ref(null)
const isUploading = ref(false)
const formBukti = reactive({
    foto: null,
    catatan: ''
})

const kembali = () => {
    router.push('/kurir/tugas-saya')
}

const muatDetail = async () => {
    isLoading.value = true
    try {
        // Memanggil endpoint backend "pengiriman/{id}/" sesuai dengan views.py logistik
        const response = await api.get(`logistik/pengiriman/${pengirimanId}/`)
        detailPengiriman.value = response.data
    } catch (error) {
        console.error("Gagal memuat detail pengiriman:", error)
        alert('Gagal memuat data dari server.')
    } finally {
        isLoading.value = false
    }
}

const tandaiSampai = async (hid) => {
    try {
        await api.post(`logistik/pengiriman/${pengirimanId}/perhentian/${hid}/sampai/`)
        muatDetail()
    } catch (error) {
        alert(error.response?.data?.detail || 'Gagal mengubah status perhentian.')
    }
}

const bukaModalBukti = (stop) => {
    titikTerpilih.value = stop
    formBukti.foto = null
    formBukti.catatan = ''
    modalBuktiAktif.value = true
}

const handleFilePilih = (e) => {
    if (e.target.files.length > 0) {
        formBukti.foto = e.target.files[0]
    }
}

const kirimBuktiTerima = async () => {
    if (!formBukti.foto || !titikTerpilih.value) return

    isUploading.value = true
    const formData = new FormData()
    formData.append('foto', formBukti.foto)
    formData.append('catatan', formBukti.catatan)

    const idemKey = 'idem-' + Date.now() + '-' + Math.random().toString(36).substring(2)
    try {
        await api.post(
            `logistik/pengiriman/${pengirimanId}/perhentian/${titikTerpilih.value.id}/bukti/`,
            formData,
            {
                headers: {
                    'Content-Type': 'multipart/form-data',
                    'Idempotency-Key': idemKey
                }
            }
        )
        alert('Bukti terima berhasil diunggah!')
        modalBuktiAktif.value = false
        muatDetail()
    } catch (error) {
        alert(error.response?.data?.detail || 'Gagal mengunggah foto bukti.')
    } finally {
        isUploading.value = false
    }
}

// Styling Badge
const getBadgeStatus = (status) => {
    if (status === 'BERANGKAT') return 'bg-blue-50 text-blue-600 border-blue-200'
    if (status === 'SELESAI') return 'bg-emerald-50 text-emerald-600 border-emerald-200'
    return 'bg-slate-100 text-slate-600 border-slate-200'
}

const getBadgeStopStatus = (status) => {
    if (status === 'DITERIMA') return 'bg-emerald-50 text-emerald-600 border-emerald-200'
    if (status === 'SAMPAI') return 'bg-amber-50 text-amber-600 border-amber-200'
    return 'bg-slate-100 text-slate-500 border-slate-200'
}

onMounted(() => {
    muatDetail()
})
</script>

<style scoped>
.max-w-md {
    max-width: 414px !important;
}

@media (min-width: 640px) {
    .max-w-md {
        margin-top: 2rem;
        margin-bottom: 2rem;
        border-radius: 2.5rem;
        overflow: hidden;
        min-height: 800px;
    }
}

.custom-scrollbar::-webkit-scrollbar {
    width: 4px;
}

.custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 999px;
}
</style>