<script setup>
import { ref } from 'vue'
import { useDocument } from '@/features/accounting/composables/useDocument'

const {
    isLoading,
    searchQuery,
    statusFilter,
    uploadForm,
    totalTransactions,
    fullyCompliantCount,
    missingDocsCount,
    filteredAuditData,
    getComplianceStats,
    handleUploadDocument,
    hapusDokumen
} = useDocument()

const showUploadModal = ref(false)
const showDetailModal = ref(false)
const selectedAuditItem = ref(null)
const isSubmitting = ref(false) // State untuk mencegah double-submit

// Kunci = field di item.files, nilai = document_type yang dikirim ke backend
const JENIS_DOKUMEN = {
    invoice: 'Invoice',
    faktur_pajak: 'Faktur Pajak',
    surat_jalan: 'Surat Jalan'
}

// statusTagihan() mengembalikan kode huruf besar (PAID/PARTIAL/OVERDUE)
const getPaymentBadge = (status) => {
    const st = String(status).toUpperCase()
    if (st === 'PAID') return 'bg-emerald-100 text-emerald-700 border border-emerald-200'
    if (st === 'PARTIAL') return 'bg-blue-100 text-blue-700 border border-blue-200'
    if (st === 'OVERDUE') return 'bg-red-100 text-red-700 border border-red-200'
    return 'bg-amber-100 text-amber-700 border border-amber-200'
}

const openDetailModal = (item) => {
    selectedAuditItem.value = item
    showDetailModal.value = true
}

const submitUpload = async () => {
    isSubmitting.value = true
    const success = await handleUploadDocument()
    if (success) {
        alert('Dokumen berhasil diunggah dan disimpan ke database!')
        showUploadModal.value = false
    }
    isSubmitting.value = false
}

const hapusDokumenModal = (type) => hapusDokumen(selectedAuditItem.value, type)

const openUploadModalFor = (po_id, partner, docType) => {
    uploadForm.po_reference = po_id
    uploadForm.partner_name = partner
    uploadForm.document_type = docType
    uploadForm.document_number = ''
    showUploadModal.value = true
}
</script>

<template>
    <div class="space-y-4 md:space-y-6 animate-fade-in text-slate-700 w-full overflow-hidden">

        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
                <h2 class="text-xl md:text-2xl font-bold text-slate-800 tracking-tight">Document Control & Audit</h2>
                <p class="text-slate-500 text-xs md:text-sm mt-1">Monitoring kelengkapan berkas legal pengiriman dan
                    penagihan.</p>
            </div>

            <button @click="showUploadModal = true"
                class="w-full sm:w-auto justify-center px-5 py-3 md:py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-bold rounded-xl shadow-md transition-all flex items-center gap-2">
                <i class="pi pi-cloud-upload text-base"></i>
                <span>Upload Dokumen Baru</span>
            </button>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-5">
            <div class="bg-white border border-slate-200 rounded-[20px] p-4 md:p-5 flex items-center gap-4 shadow-sm">
                <div
                    class="w-11 h-11 bg-slate-50 text-slate-600 rounded-xl flex items-center justify-center shrink-0 border border-slate-100">
                    <i class="pi pi-folder text-lg"></i>
                </div>
                <div>
                    <p class="text-[10px] md:text-xs font-bold text-slate-400 uppercase tracking-wider">Total Transaksi
                    </p>
                    <h3 class="text-lg md:text-xl font-black text-slate-800 mt-0.5">{{ totalTransactions }} Rute</h3>
                </div>
            </div>

            <div class="bg-white border border-slate-200 rounded-[20px] p-4 md:p-5 flex items-center gap-4 shadow-sm">
                <div
                    class="w-11 h-11 bg-emerald-50 text-emerald-600 rounded-xl flex items-center justify-center shrink-0 border border-emerald-100">
                    <i class="pi pi-verified text-lg"></i>
                </div>
                <div>
                    <p class="text-[10px] md:text-xs font-bold text-slate-400 uppercase tracking-wider">Audit Pass</p>
                    <h3 class="text-lg md:text-xl font-black text-emerald-600 mt-0.5">{{ fullyCompliantCount }} Lengkap
                    </h3>
                </div>
            </div>

            <div class="bg-white border border-slate-200 rounded-[20px] p-4 md:p-5 flex items-center gap-4 shadow-sm">
                <div
                    class="w-11 h-11 bg-amber-50 text-amber-600 rounded-xl flex items-center justify-center shrink-0 border border-amber-100">
                    <i class="pi pi-exclamation-triangle text-lg"></i>
                </div>
                <div>
                    <p class="text-[10px] md:text-xs font-bold text-slate-400 uppercase tracking-wider">Missing Docs</p>
                    <h3 class="text-lg md:text-xl font-black text-amber-600 mt-0.5">{{ missingDocsCount }} Pending</h3>
                </div>
            </div>
        </div>

        <div
            class="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4 bg-white p-3 md:p-4 border border-slate-200 rounded-2xl shadow-sm">

            <div
                class="flex bg-slate-100 p-1 rounded-xl w-full lg:w-auto overflow-x-auto custom-scrollbar no-scrollbar-mobile">
                <button @click="statusFilter = 'all'"
                    :class="statusFilter === 'all' ? 'bg-white text-slate-900 shadow-sm font-bold' : 'text-slate-500 hover:text-slate-800'"
                    class="px-4 py-2 text-xs rounded-lg transition-all whitespace-nowrap flex-1 lg:flex-none text-center">Semua
                    Berkas</button>
                <button @click="statusFilter = 'lengkap'"
                    :class="statusFilter === 'lengkap' ? 'bg-white text-emerald-600 shadow-sm font-bold' : 'text-slate-500 hover:text-slate-800'"
                    class="px-4 py-2 text-xs rounded-lg transition-all whitespace-nowrap flex-1 lg:flex-none text-center">Lengkap</button>
                <button @click="statusFilter = 'tidak_lengkap'"
                    :class="statusFilter === 'tidak_lengkap' ? 'bg-white text-amber-600 shadow-sm font-bold' : 'text-slate-500 hover:text-slate-800'"
                    class="px-4 py-2 text-xs rounded-lg transition-all whitespace-nowrap flex-1 lg:flex-none text-center">Pending</button>
            </div>

            <div class="relative w-full lg:w-72">
                <i class="pi pi-search absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-xs"></i>
                <input type="text" v-model="searchQuery" placeholder="Cari No. PO / Supplier..."
                    class="w-full pl-9 pr-4 py-2.5 md:py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs md:text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 text-slate-700" />
            </div>
        </div>

        <div class="w-full">
            <table class="w-full text-left text-sm border-collapse">
                <thead
                    class="hidden md:table-header-group bg-slate-50 text-slate-500 border border-slate-200 rounded-t-2xl">
                    <tr>
                        <th class="py-4 px-6 font-semibold rounded-tl-2xl">Referensi Transaksi</th>
                        <th class="py-4 px-4 font-semibold text-center">1. Invoice</th>
                        <th class="py-4 px-4 font-semibold text-center">2. Faktur Pajak</th>
                        <th class="py-4 px-4 font-semibold text-center">3. Surat Jalan</th>
                        <th class="py-4 px-6 font-semibold text-center">Status Audit</th>
                        <th class="py-4 px-4 font-semibold text-center">Pembayaran</th>
                        <th class="py-4 px-4 font-semibold text-center rounded-tr-2xl">Aksi</th>
                    </tr>
                </thead>

                <tbody
                    class="block md:table-row-group bg-transparent md:bg-white md:border md:border-t-0 md:border-slate-200 rounded-b-2xl">
                    <tr v-for="item in filteredAuditData" :key="item.po_id"
                        class="block md:table-row bg-white border border-slate-200 md:border-b md:border-x-0 md:border-t-0 md:border-slate-100 hover:bg-slate-50/40 transition-colors rounded-2xl md:rounded-none mb-4 md:mb-0 p-4 md:p-0 shadow-sm md:shadow-none relative">

                        <td
                            class="block md:table-cell md:py-4 md:px-6 mb-4 md:mb-0 border-b border-slate-50 md:border-none pb-3 md:pb-0">
                            <p class="text-sm font-black text-slate-800">{{ item.po_id }}</p>
                            <p class="text-xs text-slate-500 mt-0.5">{{ item.partner }}</p>
                            <p class="text-[10px] text-slate-400 mt-0.5">{{ item.date }}</p>
                        </td>

                        <td v-for="(label, key, idx) in JENIS_DOKUMEN" :key="key"
                            class="flex justify-between items-center md:table-cell py-2 md:py-4 md:px-4 md:text-center border-b border-slate-50 md:border-none">
                            <span class="md:hidden text-xs font-bold text-slate-500">{{ idx + 1 }}. {{ label }}</span>
                            <span v-if="item.files[key]?.exists"
                                class="inline-block px-2 py-0.5 bg-emerald-50 text-emerald-700 text-[10px] font-bold rounded border border-emerald-100">
                                {{ item.files[key].doc_no }}
                            </span>
                            <button v-else @click="openUploadModalFor(item.po_id, item.partner, label)"
                                class="px-2 py-0.5 text-[10px] font-bold text-slate-400 hover:text-emerald-600 border border-dashed border-slate-300 hover:border-emerald-400 rounded transition-colors">
                                <i class="pi pi-plus text-[9px] mr-1"></i>Upload
                            </button>
                        </td>

                        <td class="block md:table-cell md:py-4 md:px-6 md:text-center mb-3 md:mb-0">
                            <div class="flex items-center gap-2 md:justify-center">
                                <div class="w-full md:w-20 bg-slate-200 h-1.5 rounded-full overflow-hidden">
                                    <div :class="getComplianceStats(item.files).isComplete ? 'bg-emerald-500' : 'bg-amber-500'"
                                        :style="{ width: getComplianceStats(item.files).percentage + '%' }"
                                        class="h-full transition-all duration-500"></div>
                                </div>
                                <span class="text-[10px] font-bold text-slate-500 whitespace-nowrap">{{
                                    getComplianceStats(item.files).count }}/3</span>
                            </div>
                        </td>

                        <td
                            class="flex justify-between items-center md:table-cell md:py-4 md:px-4 md:text-center mb-4 md:mb-0">
                            <span class="md:hidden text-xs font-bold text-slate-500">Pembayaran</span>
                            <span :class="getPaymentBadge(item.payment_status)"
                                class="inline-block px-2.5 py-1 text-[10px] font-bold rounded-full">{{
                                    item.payment_status }}</span>
                        </td>

                        <td class="block md:table-cell p-0 md:py-4 md:px-4 md:text-center mt-2 md:mt-0">
                            <button @click="openDetailModal(item)"
                                class="w-full md:w-auto px-4 py-2.5 md:py-1.5 text-xs font-bold text-slate-600 bg-slate-100 hover:bg-slate-800 hover:text-white rounded-xl md:rounded-lg transition-colors">
                                <i class="pi pi-eye mr-1 text-xs"></i>Detail
                            </button>
                        </td>

                    </tr>
                </tbody>
            </table>
        </div>

        <div v-if="showUploadModal"
            class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4"
            @click.self="showUploadModal = false">
            <div
                class="bg-white w-full max-w-md max-h-[95vh] overflow-y-auto rounded-[24px] shadow-2xl flex flex-col animate-fade-in-up">
                <div
                    class="px-5 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50/50 sticky top-0 z-10">
                    <h3 class="text-sm md:text-base font-bold text-slate-800">Upload Berkas Pendukung</h3>
                    <button @click="showUploadModal = false" :disabled="isSubmitting"
                        class="text-slate-400 hover:text-red-500 transition-colors disabled:opacity-50"><i
                            class="pi pi-times text-lg"></i></button>
                </div>

                <div class="p-5 space-y-4">
                    <div class="flex flex-col gap-1.5">
                        <label class="text-xs font-bold text-slate-500">REFERENSI NO. PO / ID</label>
                        <input type="text" v-model="uploadForm.po_reference" placeholder="PO-2026-..."
                            class="w-full px-4 py-3 md:py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 text-slate-800 uppercase" />
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div class="flex flex-col gap-1.5">
                            <label class="text-xs font-bold text-slate-500">JENIS DOKUMEN</label>
                            <select v-model="uploadForm.document_type"
                                class="w-full px-4 py-3 md:py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 text-slate-800">
                                <option value="Invoice">1. Invoice</option>
                                <option value="Faktur Pajak">2. Faktur Pajak</option>
                                <option value="Surat Jalan">3. Surat Jalan</option>
                            </select>
                        </div>
                        <div class="flex flex-col gap-1.5">
                            <label class="text-xs font-bold text-slate-500">NOMOR DOKUMEN</label>
                            <input type="text" v-model="uploadForm.document_number" placeholder="No. Seri Berkas..."
                                class="w-full px-4 py-3 md:py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 text-slate-800" />
                        </div>
                    </div>

                    <div class="flex flex-col gap-1.5">
                        <label class="text-xs font-bold text-slate-500">NAMA SUPPLIER</label>
                        <input type="text" v-model="uploadForm.partner_name"
                            class="w-full px-4 py-3 md:py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 text-slate-800" />
                    </div>
                </div>

                <div class="px-5 py-4 border-t border-slate-100 flex justify-end gap-3 bg-slate-50/50 sticky bottom-0">
                    <button @click="showUploadModal = false" :disabled="isSubmitting"
                        class="flex-1 md:flex-none px-4 py-3 md:py-2 text-sm md:text-xs font-bold text-slate-600 bg-white border border-slate-200 rounded-xl hover:bg-slate-50 disabled:opacity-50">Batal</button>
                    <!-- Tombol Upload terhubung ke submitUpload() dengan state isSubmitting -->
                    <button @click="submitUpload" :disabled="isSubmitting"
                        class="flex-1 md:flex-none px-4 py-3 md:py-2 text-sm md:text-xs font-bold text-white bg-emerald-600 rounded-xl hover:bg-emerald-700 shadow-md disabled:opacity-50 disabled:cursor-not-allowed">
                        <i v-if="isSubmitting" class="pi pi-spin pi-spinner mr-1"></i>
                        {{ isSubmitting ? 'Mengarsipkan...' : 'Arsipkan Dokumen' }}
                    </button>
                </div>
            </div>
        </div>

        <div v-if="showDetailModal && selectedAuditItem"
            class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4"
            @click.self="showDetailModal = false">
            <div
                class="bg-white w-full max-w-3xl max-h-[95vh] overflow-y-auto rounded-[24px] shadow-2xl flex flex-col animate-fade-in-up">

                <div
                    class="px-5 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50/50 sticky top-0 z-10">
                    <h3 class="text-sm md:text-base font-bold text-slate-800">Detail Transaksi Audit</h3>
                    <button @click="showDetailModal = false"
                        class="w-8 h-8 rounded-full bg-slate-100 text-slate-500 hover:text-red-500 transition-colors flex items-center justify-center"><i
                            class="pi pi-times text-sm"></i></button>
                </div>

                <div class="p-5 grid grid-cols-1 md:grid-cols-2 gap-6 bg-white">
                    <div>
                        <h4 class="text-sm font-bold text-slate-800 mb-3 flex items-center gap-2"><i
                                class="pi pi-info-circle text-emerald-500"></i> Informasi Transaksi</h4>
                        <div class="bg-slate-50 border border-slate-200 rounded-2xl p-4 space-y-4">
                            <div>
                                <p class="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">REFERENSI
                                    PO</p>
                                <p class="text-base md:text-lg font-black text-slate-800">{{ selectedAuditItem.po_id }}
                                </p>
                            </div>
                            <div class="grid grid-cols-2 gap-4">
                                <div>
                                    <p class="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">
                                        TANGGAL</p>
                                    <p class="text-xs md:text-sm font-bold text-slate-700">{{ selectedAuditItem.date }}
                                    </p>
                                </div>
                                <div>
                                    <p class="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">
                                        REKANAN</p>
                                    <p class="text-xs md:text-sm font-bold text-slate-700">{{ selectedAuditItem.partner
                                    }}</p>
                                </div>
                            </div>
                            <div class="pt-3 border-t border-slate-200">
                                <div class="flex items-center justify-between mb-1.5">
                                    <span class="text-[11px] md:text-xs font-bold"
                                        :class="getComplianceStats(selectedAuditItem.files).isComplete ? 'text-emerald-600' : 'text-amber-600'">
                                        {{ getComplianceStats(selectedAuditItem.files).isComplete ? 'Lengkap 100%' :
                                            'Belum Lengkap' }}
                                    </span>
                                    <span class="text-[10px] md:text-xs font-bold text-slate-500">{{
                                        getComplianceStats(selectedAuditItem.files).count }} / 3 Berkas</span>
                                </div>
                                <div class="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
                                    <div :class="getComplianceStats(selectedAuditItem.files).isComplete ? 'bg-emerald-500' : 'bg-amber-500'"
                                        :style="{ width: getComplianceStats(selectedAuditItem.files).percentage + '%' }"
                                        class="h-full transition-all duration-500"></div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div>
                        <h4 class="text-sm font-bold text-slate-800 mb-3 flex items-center gap-2"><i
                                class="pi pi-folder-open text-emerald-500"></i> Kelengkapan Berkas</h4>
                        <div class="space-y-3">
                            <div v-for="(file, key, idx) in selectedAuditItem.files" :key="key"
                                class="bg-white border border-slate-200 rounded-xl p-3 flex items-center justify-between shadow-sm">
                                <div>
                                    <p class="text-xs font-bold text-slate-800 mb-1 capitalize">{{ idx + 1 }}. {{
                                        key.replace('_', ' ') }}</p>
                                    <span v-if="file?.exists"
                                        class="inline-block px-2 py-0.5 bg-emerald-50 text-emerald-700 text-[10px] font-bold rounded border border-emerald-100">
                                        {{ file.doc_no }}
                                    </span>
                                    <span v-else
                                        class="inline-block px-2 py-0.5 bg-red-50 text-red-600 text-[10px] font-bold rounded border border-red-100">Belum
                                        Ada</span>
                                </div>
                                <div v-if="file?.exists" class="flex items-center gap-2">
                                    <button
                                        class="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 hover:bg-emerald-600 hover:text-white transition-colors flex items-center justify-center"><i
                                            class="pi pi-download text-xs"></i></button>
                                    <!-- hapusDokumenModal terhubung ke backend delete -->
                                    <button @click="hapusDokumenModal(key)" :disabled="isLoading"
                                        class="w-8 h-8 rounded-lg bg-red-50 text-red-500 hover:bg-red-500 hover:text-white transition-colors flex items-center justify-center disabled:opacity-50"><i
                                            class="pi pi-trash text-xs"></i></button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="px-5 py-4 border-t border-slate-100 flex justify-end bg-slate-50/50 sticky bottom-0">
                    <button @click="showDetailModal = false"
                        class="w-full md:w-auto px-6 py-3 md:py-2.5 text-sm md:text-xs font-bold text-white bg-slate-800 rounded-xl hover:bg-slate-900 shadow-md">Tutup
                        Panel</button>
                </div>
            </div>
        </div>

    </div>
</template>

<style scoped>
.animate-fade-in {
    animation: fadeIn 0.4s ease-out;
}

.animate-fade-in-up {
    animation: fadeInUp 0.3s ease-out;
}

@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(5px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(15px) scale(0.98);
    }

    to {
        opacity: 1;
        transform: translateY(0) scale(1);
    }
}

.no-scrollbar-mobile::-webkit-scrollbar {
    display: none;
}

.no-scrollbar-mobile {
    -ms-overflow-style: none;
    scrollbar-width: none;
}
</style>