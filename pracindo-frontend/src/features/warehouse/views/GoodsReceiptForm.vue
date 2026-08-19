<!-- features/warehouse/views/GoodsReceiptForm.vue -->
<template>
    <div class="flex flex-col w-full animate-fade-in relative">
        <!-- STATE 1: SUKSES DISIMPAN -->
        <template v-if="hasil">
            <section class="bg-white border border-emerald-200 rounded-[24px] p-6 md:p-8 shadow-sm w-full">
                <div class="flex items-center gap-3 mb-2">
                    <div class="w-10 h-10 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center">
                        <i class="pi pi-check text-xl"></i>
                    </div>
                    <h1 class="text-xl md:text-2xl font-bold text-slate-800 tracking-tight">Penerimaan Tersimpan</h1>
                </div>
                <p class="text-sm text-slate-600 mb-4 ml-13">{{ hasil.pesan }}</p>

                <!-- ... (Data Detail Sukses sama persis seperti file lama) ... -->

                <!-- PERBAIKAN: Tombol Aksi Emit Tutup -->
                <div class="flex flex-col sm:flex-row gap-3 ml-0 md:ml-13 mt-6">
                    <router-link v-if="hasil.penerimaan?.id" :to="`/warehouse/penerimaan/${hasil.penerimaan.id}`"
                        class="px-6 py-2.5 bg-slate-900 hover:bg-slate-800 text-white text-sm font-bold rounded-xl transition-colors shadow-md text-center">
                        Lihat Detail
                    </router-link>
                    <button type="button" @click="$emit('tutup')"
                        class="px-6 py-2.5 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 text-sm font-bold rounded-xl transition-colors text-center">
                        Kembali ke Daftar
                    </button>
                </div>
            </section>
        </template>

        <!-- STATE 2: FORMULIR INPUT -->
        <form v-else @submit.prevent="kirim" class="space-y-6">
            <!-- Panel 1: Info PO & Surat Jalan -->
            <section class="bg-white border border-slate-200 rounded-[24px] p-4 md:p-6 shadow-sm w-full">
                <!-- ... (Input PO dan SJ sama persis seperti file lama) ... -->
            </section>

            <!-- Panel 2: Tabel Input Item -->
            <section v-if="poTerpilih" class="bg-white border border-slate-200 rounded-[24px] p-4 md:p-6 shadow-sm w-full animate-fade-in">
                <!-- ... (Tabel Item dan Card Item sama persis seperti file lama) ... -->

                <!-- Area Error Global & Tombol Submit -->
                <div class="mt-8 pt-6 border-t border-slate-100">
                    <div v-if="pesanError" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-600 font-bold flex items-center gap-2">
                        <i class="pi pi-exclamation-circle"></i> {{ pesanError }}
                    </div>

                    <!-- PERBAIKAN: Tombol Batal Emit Tutup -->
                    <div class="flex justify-end gap-3">
                        <button type="button" @click="$emit('tutup')"
                            class="px-6 py-3 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 text-sm font-bold rounded-xl transition-colors">
                            Batal
                        </button>
                        <button type="submit" :disabled="sedangProses || barisLewatSisa.length > 0"
                            class="px-8 py-3 bg-slate-900 hover:bg-slate-800 disabled:bg-slate-300 text-white text-sm font-bold rounded-xl shadow-md transition-all flex items-center gap-2 cursor-pointer disabled:cursor-not-allowed transform hover:-translate-y-0.5">
                            <i v-if="sedangProses" class="pi pi-spin pi-spinner text-xs"></i>
                            <i v-else class="pi pi-save text-xs"></i>
                            {{ sedangProses ? 'Menyimpan...' : 'Simpan Penerimaan' }}
                        </button>
                    </div>
                </div>
            </section>
        </form>
    </div>
</template>

<script setup>
// Tambahkan deklarasi emit untuk mengendalikan lazy view dari induk
const emit = defineEmits(['tutup'])

// ... (seluruh baris import dan deklarasi logic script sisanya sama persis seperti kode Anda sebelumnya) ...
</script>
