<template>
    <div class="flex flex-col w-full animate-fade-in relative max-w-md mx-auto min-h-screen bg-slate-50">
        <div class="bg-slate-900 pt-8 pb-6 px-6 shadow-md text-white sticky top-0 z-30">
            <div class="flex items-center justify-between">
                <div class="flex items-center gap-4">
                    <button @click="$router.push('/kurir/tugas-saya')" class="w-10 h-10 bg-slate-800 rounded-xl flex items-center justify-center hover:bg-slate-700 transition-colors">
                        <i class="pi pi-arrow-left text-sm"></i>
                    </button>
                    <div>
                        <h1 class="text-lg font-black tracking-tight line-clamp-1">{{ tugas?.no_do || 'Detail Tugas' }}</h1>
                        <p class="text-[10px] text-slate-400 mt-0.5 uppercase tracking-wider">Informasi Pengiriman</p>
                    </div>
                </div>
                <span v-if="tugas" class="px-2.5 py-1 rounded-md text-[10px] font-black tracking-widest uppercase border bg-slate-800 border-slate-700 text-slate-300">
                    {{ tugas.status_tampil }}
                </span>
            </div>
        </div>

        <div v-if="sedangMemuat" class="py-12 flex justify-center">
            <i class="pi pi-spin pi-spinner text-3xl text-blue-500"></i>
        </div>

        <div v-else-if="tugas" class="p-5 flex-col gap-5 flex pb-32">
            <div class="bg-white border border-slate-200 rounded-[20px] p-5 shadow-sm">
                <div class="flex items-center gap-3 mb-4 pb-4 border-b border-slate-100">
                    <div class="w-12 h-12 bg-blue-50 text-blue-600 rounded-full flex items-center justify-center">
                        <i class="pi pi-map-marker text-xl"></i>
                    </div>
                    <div>
                        <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-0.5">Penerima</span>
                        <p class="text-sm font-bold text-slate-800">{{ tugas.tujuan_nama }}</p>
                    </div>
                </div>
                <div>
                    <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Alamat Lengkap</span>
                    <p class="text-sm text-slate-600 leading-relaxed">{{ tugas.tujuan_alamat }}</p>
                </div>
                <button class="mt-4 w-full py-2.5 bg-slate-100 text-slate-700 hover:bg-slate-200 text-xs font-bold rounded-xl transition-colors flex items-center justify-center gap-2 border border-slate-200">
                    <i class="pi pi-map"></i> Buka di Google Maps
                </button>
            </div>

            <div v-if="tugas.status_perhentian === 'SAMPAI'" class="bg-white border border-slate-200 rounded-[20px] p-5 shadow-sm">
                <h3 class="text-sm font-bold text-slate-800 mb-4">Bukti Pengiriman (POD)</h3>
                <div class="flex flex-col gap-4">
                    <div class="flex flex-col gap-1.5">
                        <label class="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Nama Penerima</label>
                        <input type="text" v-model="formPOD.penerima" placeholder="Nama orang yang menerima..."
                            class="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 text-slate-800 font-medium" />
                    </div>
                    <div class="flex flex-col gap-1.5">
                        <label class="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Foto Barang / Surat Jalan</label>
                        <label class="w-full h-32 border-2 border-dashed border-slate-300 rounded-xl bg-slate-50 flex flex-col items-center justify-center cursor-pointer hover:bg-slate-100 hover:border-emerald-500 transition-colors group">
                            <i class="pi pi-camera text-2xl text-slate-400 group-hover:text-emerald-500 mb-2"></i>
                            <span class="text-xs font-bold text-slate-500 group-hover:text-emerald-600">Ambil Foto</span>
                            <input type="file" accept="image/*" class="hidden" @change="handleFotoUpload" />
                        </label>
                        <p v-if="formPOD.foto" class="text-xs text-emerald-600 font-bold mt-1 text-center"><i class="pi pi-check-circle"></i> File siap diunggah</p>
                    </div>
                </div>
            </div>
        </div>

        <div v-if="tugas" class="fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 p-4 shadow-[0_-4px_20px_rgba(0,0,0,0.05)] z-40 max-w-md mx-auto">
            <button v-if="tugas.status_pengiriman === 'DISIAPKAN'" @click="aksiBerangkat"
                class="w-full py-3.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-bold rounded-xl shadow-md transition-colors flex justify-center items-center gap-2">
                <i class="pi pi-play text-xs"></i> Mulai Perjalanan
            </button>
            <button v-else-if="tugas.status_perhentian === 'MENUNGGU'" @click="aksiTiba"
                class="w-full py-3.5 bg-amber-500 hover:bg-amber-600 text-white text-sm font-bold rounded-xl shadow-md transition-colors flex justify-center items-center gap-2">
                <i class="pi pi-stop-circle text-xs"></i> Tiba di Lokasi
            </button>
            <button v-else-if="tugas.status_perhentian === 'SAMPAI'" @click="aksiKirimPOD" :disabled="!formPOD.penerima || !formPOD.foto"
                class="w-full py-3.5 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-bold rounded-xl shadow-md transition-colors flex justify-center items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed">
                <i class="pi pi-cloud-upload text-xs"></i> Selesaikan Tugas
            </button>
            <div v-else-if="['DITERIMA', 'DIRETUR'].includes(tugas.status_perhentian)"
                class="w-full py-3.5 bg-slate-100 text-slate-500 text-sm font-bold rounded-xl flex justify-center items-center gap-2 border border-slate-200 cursor-not-allowed">
                <i class="pi pi-check-circle text-emerald-500"></i> Tugas Selesai
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useCourier } from '../composables/useCourier'

const route = useRoute()
const router = useRouter()
const { daftarPengiriman, sedangMemuat, muatTugas, berangkatkan, tandaiSampai, unggahBukti } = useCourier()

const formPOD = reactive({ penerima: '', foto: null })
const pId = computed(() => route.query.pengiriman)
const hId = computed(() => route.params.id)

const tugas = computed(() => {
    for (const kirim of daftarPengiriman.value) {
        if (String(kirim.id) === String(pId.value)) {
            const stop = kirim.perhentian?.find(s => String(s.id) === String(hId.value))
            if (stop) {
                let statusTampil = stop.status
                if (kirim.status === 'DISIAPKAN') statusTampil = 'SIAP JALAN'
                else if (stop.status === 'MENUNGGU' && kirim.status === 'BERANGKAT') statusTampil = 'OTW'

                return {
                    pengiriman_id: kirim.id,
                    perhentian_id: stop.id,
                    no_do: stop.nomor_distribusi || 'DO-SYSTEM',
                    tujuan_nama: stop.pelanggan_nama || stop.pelanggan,
                    tujuan_alamat: stop.alamat,
                    status_pengiriman: kirim.status,
                    status_perhentian: stop.status,
                    status_tampil: statusTampil
                }
            }
        }
    }
    return null
})

const aksiBerangkat = async () => {
    if (confirm("Mulai perjalanan ini?")) {
        await berangkatkan(tugas.value.pengiriman_id)
    }
}

const aksiTiba = async () => {
    await tandaiSampai(tugas.value.pengiriman_id, tugas.value.perhentian_id)
}

const handleFotoUpload = (e) => {
    if (e.target.files.length > 0) {
        formPOD.foto = e.target.files[0]
    }
}

const aksiKirimPOD = async () => {
    const res = await unggahBukti(tugas.value.pengiriman_id, tugas.value.perhentian_id, formPOD.foto, formPOD.penerima)
    if (res.success) {
        alert('Bukti pengiriman (POD) berhasil diunggah!')
        router.push('/kurir/tugas-saya')
    } else {
        alert('Gagal mengunggah bukti.')
    }
}

onMounted(() => {
    if (daftarPengiriman.value.length === 0) {
        muatTugas()
    }
})
</script>

<style scoped>
.animate-fade-in { animation: fadeIn 0.3s ease-out forwards; }
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
</style>
