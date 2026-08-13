<template>
    <div class="max-w-4xl mx-auto p-4 md:p-6 lg:p-8 animate-fade-in">
        <header class="mb-8">
            <h1 class="text-2xl font-black text-slate-800 flex items-center gap-3">
                <i class="pi pi-box text-indigo-600"></i> Pengepakan (Packaging)
            </h1>
            <p class="text-sm text-slate-500 mt-1 ml-9">
                Proses konversi curah (POOL) menjadi SKU Barang Jadi. Hak kepemilikan Entitas akan dipotong secara
                proporsional.
            </p>
        </header>

        <div v-if="galat"
            class="mb-6 p-4 bg-red-50 border-l-4 border-red-500 text-red-800 rounded-r-md text-sm font-semibold">
            {{ galat }}
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-5 gap-8">
            <!-- AREA FORM INPUT -->
            <div class="lg:col-span-3 space-y-6">
                <!-- Blok Dokumen -->
                <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-4">
                    <h2 class="text-xs font-black tracking-wider text-slate-400 uppercase mb-2">Informasi Pengepakan
                    </h2>
                    <div class="grid grid-cols-2 gap-4">
                        <label class="flex flex-col gap-1.5">
                            <span class="text-sm font-bold text-slate-700">Tanggal</span>
                            <input type="date" v-model="form.tanggal"
                                class="p-2 bg-slate-50 border border-slate-200 rounded-lg text-sm outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500">
                        </label>
                        <label class="flex flex-col gap-1.5">
                            <span class="text-sm font-bold text-slate-700">Referensi / No. Batch</span>
                            <input type="text" v-model="form.referensi" placeholder="Otomatis jika kosong"
                                class="p-2 bg-slate-50 border border-slate-200 rounded-lg text-sm outline-none focus:border-indigo-500">
                        </label>
                    </div>

                    <label class="flex flex-col gap-1.5">
                        <span class="text-sm font-bold text-slate-700">Entitas Pemilik Hak</span>
                        <select v-model="form.entitas_id"
                            class="p-2 bg-slate-50 border border-slate-200 rounded-lg text-sm outline-none focus:border-indigo-500"
                            :disabled="memuat.awal">
                            <option value="">-- Pilih Entitas yang dikurangi haknya --</option>
                            <option v-for="e in opsi.entitas" :key="e.id" :value="e.id">{{ e.kode }} - {{ e.nama }}
                            </option>
                        </select>
                    </label>
                </div>

                <!-- Blok Detail Kemasan -->
                <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-4"
                    :class="{ 'opacity-50 pointer-events-none': !form.entitas_id }">
                    <h2 class="text-xs font-black tracking-wider text-slate-400 uppercase mb-2">Target Konversi</h2>

                    <label class="flex flex-col gap-1.5">
                        <span class="text-sm font-bold text-slate-700">Pilih SKU Kemasan</span>
                        <select v-model="form.kemasan_id"
                            class="p-2 bg-slate-50 border border-slate-200 rounded-lg text-sm outline-none focus:border-indigo-500">
                            <option value="">-- Pilih --</option>
                            <option v-for="k in opsi.kemasan" :key="k.id" :value="k.id">{{ k.nama_kemasan }}</option>
                        </select>
                    </label>

                    <label class="flex flex-col gap-1.5">
                        <span class="text-sm font-bold text-slate-700">Sumber Tangki WIP (POOL)</span>
                        <select v-model="form.tangki_pool_id"
                            class="p-2 bg-slate-50 border border-slate-200 rounded-lg text-sm outline-none focus:border-indigo-500">
                            <option value="">Sembarang Tangki (Sistem akan mencari otomatis)</option>
                            <option v-for="t in tangkiSesuaiGrup" :key="t.id" :value="t.id">{{ t.kode }} - {{ t.nama }}
                            </option>
                        </select>
                    </label>

                    <div class="grid grid-cols-2 gap-4">
                        <label class="flex flex-col gap-1.5">
                            <span class="text-sm font-bold text-slate-700">Jumlah Hasil (PCS)</span>
                            <input type="number" v-model="form.jumlah" placeholder="0"
                                class="p-2 bg-slate-50 border border-slate-200 rounded-lg text-lg font-mono text-right outline-none focus:border-indigo-500 font-bold">
                        </label>
                        <label class="flex flex-col gap-1.5"
                            title="Isi jika hasil timbangan selang/tetesan berbeda dari standar kemasan">
                            <span class="text-sm font-bold text-slate-700">Timbangan Curah (KG)</span>
                            <input type="number" v-model="form.qty_curah_aktual" placeholder="Opsional"
                                class="p-2 bg-slate-50 border border-slate-200 rounded-lg text-lg font-mono text-right outline-none focus:border-indigo-500 text-slate-500 placeholder-slate-300">
                            <span class="text-[10px] text-slate-400 text-right uppercase">Aktual yg Keluar</span>
                        </label>
                    </div>
                </div>
            </div>

            <!-- AREA PREVIEW (NERACA) -->
            <div class="lg:col-span-2">
                <div
                    class="bg-slate-800 text-white rounded-2xl shadow-lg overflow-hidden sticky top-8 flex flex-col h-[calc(100%-2rem)]">
                    <div class="p-5 border-b border-slate-700 bg-slate-900/50">
                        <h2 class="text-sm font-black tracking-wider text-slate-400 uppercase flex items-center gap-2">
                            <i class="pi pi-calculator"></i> Pratinjau Aliran
                            <i v-if="memuat.rencana" class="pi pi-spin pi-spinner ml-auto text-indigo-400"></i>
                        </h2>
                    </div>

                    <div class="p-6 flex-1 flex flex-col justify-center">
                        <template v-if="pratinjau">
                            <div class="space-y-6">
                                <!-- Status Cukup/Tidak -->
                                <div class="text-center p-3 rounded-lg border"
                                    :class="pratinjau.cukup ? 'bg-emerald-900/30 border-emerald-500/30 text-emerald-400' : 'bg-red-900/30 border-red-500/30 text-red-400'">
                                    <div class="text-xs font-bold uppercase mb-1">Status Ketersediaan</div>
                                    <div class="text-sm">{{ pratinjau.cukup ? 'Tangki Cukup' : pratinjau.pesan || 'Stok
                                        Curah Kurang' }}</div>
                                </div>

                                <div class="flex justify-between items-center border-b border-slate-700 pb-3">
                                    <span class="text-slate-400 text-sm">Target Barang Jadi</span>
                                    <span class="font-mono font-bold text-xl">{{ pratinjau.jumlah }} <span
                                            class="text-xs text-slate-500">PCS</span></span>
                                </div>

                                <div class="flex justify-between items-center border-b border-slate-700 pb-3">
                                    <span class="text-slate-400 text-sm">Sumbangan Curah Keluar</span>
                                    <span class="font-mono font-bold text-xl text-amber-400">{{ pratinjau.qty_curah }}
                                        <span class="text-xs text-amber-600">KG</span></span>
                                </div>

                                <div class="flex justify-between items-center pt-2">
                                    <span class="text-slate-400 text-sm">Pemotongan Hak Klaim</span>
                                    <span class="font-mono font-bold text-lg text-emerald-400">Rp {{
                                        Number(pratinjau.nilai).toLocaleString('id-ID') }}</span>
                                </div>
                                <p class="text-[10px] text-slate-500 text-right mt-1 leading-tight">
                                    Dihitung menggunakan persentase harga rata-rata<br />isi tangki saat ini.
                                </p>
                            </div>
                        </template>
                        <template v-else>
                            <div class="text-center opacity-40 py-10">
                                <i class="pi pi-box text-5xl mb-4 block"></i>
                                <p class="text-sm font-semibold">Pilih Entitas, Kemasan, dan Jumlah untuk melihat
                                    kalkulasi nilai.</p>
                            </div>
                        </template>
                    </div>

                    <div class="p-4 bg-slate-900">
                        <button @click="kirim" :disabled="!bisaKirim"
                            class="w-full py-3.5 rounded-xl font-black text-sm uppercase tracking-wider transition-all"
                            :class="bisaKirim ? 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-[0_0_20px_rgba(79,70,229,0.4)]' : 'bg-slate-800 text-slate-600 border border-slate-700 cursor-not-allowed'">
                            {{ memuat.kirim ? 'Memproses...' : 'Eksekusi Pengemasan' }}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { usePackaging } from '../composables/usePackaging'

const emit = defineEmits(['tersimpan'])

const {
    form, opsi, memuat, pratinjau, galat, bisaKirim, tangkiSesuaiGrup,
    muatDataAwal, kirim
} = usePackaging(emit)

onMounted(() => {
    muatDataAwal()
})
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