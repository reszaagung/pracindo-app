<!-- src/views/sales/SalesCrmBoard.vue -->
<template>
    <div class="crm-dashboard animate-fade-in">
        <!-- HEADER -->
        <header class="tech-header">
            <div class="title-wrapper">
                <div class="title-icon">
                    <i class="pi pi-users"></i>
                </div>
                <div>
                    <h1>CRM & Eksekusi Sales</h1>
                    <p>Pusat kendali prospek, konversi pelanggan, dan dokumen penjualan.</p>
                </div>
            </div>

            <div class="header-actions">
                <div class="search-bar">
                    <i class="pi pi-search"></i>
                    <input type="text" placeholder="Cari kontak, nomor HP, atau perusahaan..."
                        class="neo-input search-input">
                </div>
                <button @click="bukaModalProspek" class="btn-primary-tech">
                    <i class="pi pi-user-plus"></i> <span>Tambah Prospek</span>
                </button>
            </div>
        </header>

        <!-- NAVIGATION TABS (Pilar CRM) -->
        <nav class="crm-tabs">
            <button class="tab-btn active"><i class="pi pi-address-book"></i> Pipeline Prospek</button>
            <button class="tab-btn"><i class="pi pi-file-edit"></i> Dokumen (SO & Invoice)</button>
            <button class="tab-btn"><i class="pi pi-map-marker"></i> Aktivitas & GPS Tim</button>
            <button class="tab-btn"><i class="pi pi-chart-bar"></i> Analisis Penjualan</button>
        </nav>

        <!-- KANBAN BOARD (Manajemen Prospek) -->
        <div class="kanban-board">

            <!-- KOLOM 1: LEADS (Baru Bertanya) -->
            <div class="kanban-col">
                <div class="col-header">
                    <div class="col-title">
                        <span class="dot dot-new"></span> LEADS BARU
                        <span class="count">{{ leads.length }}</span>
                    </div>
                    <button class="btn-icon-sm"><i class="pi pi-ellipsis-h"></i></button>
                </div>
                <div class="col-body custom-scroll">
                    <div v-for="lead in leads" :key="lead.id" class="kanban-card">
                        <div class="card-head">
                            <span class="company">{{ lead.perusahaan }}</span>
                            <span class="date">{{ lead.tanggal }}</span>
                        </div>
                        <h3 class="contact-name">{{ lead.nama }}</h3>
                        <div class="contact-info">
                            <span><i class="pi pi-whatsapp"></i> {{ lead.telepon }}</span>
                        </div>
                        <div class="card-foot">
                            <span class="est-value">Est: {{ formatRupiah(lead.estimasi_nilai) }}</span>
                            <button class="btn-move" title="Geser ke Negosiasi">
                                Nego <i class="pi pi-arrow-right"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- KOLOM 2: PROSPECT (Negosiasi / Follow Up) -->
            <div class="kanban-col">
                <div class="col-header">
                    <div class="col-title">
                        <span class="dot dot-nego"></span> NEGOSIASI (PROSPECT)
                        <span class="count">{{ prospects.length }}</span>
                    </div>
                    <button class="btn-icon-sm"><i class="pi pi-ellipsis-h"></i></button>
                </div>
                <div class="col-body custom-scroll">
                    <div v-for="prospect in prospects" :key="prospect.id" class="kanban-card border-nego">
                        <div class="card-head">
                            <span class="company">{{ prospect.perusahaan }}</span>
                            <span class="date text-warn"><i class="pi pi-clock"></i> Follow up besok</span>
                        </div>
                        <h3 class="contact-name">{{ prospect.nama }}</h3>
                        <div class="contact-info">
                            <span><i class="pi pi-whatsapp"></i> {{ prospect.telepon }}</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: 60%"></div>
                        </div>
                        <div class="card-foot">
                            <span class="est-value highlight">{{ formatRupiah(prospect.estimasi_nilai) }}</span>
                            <button class="btn-move success" title="Tandai Berhasil (Won)">
                                Deal <i class="pi pi-check"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- KOLOM 3: WON (Berhasil / Jadi Beli) -->
            <div class="kanban-col">
                <div class="col-header">
                    <div class="col-title">
                        <span class="dot dot-won"></span> BERHASIL (WON)
                        <span class="count">{{ won.length }}</span>
                    </div>
                    <button class="btn-icon-sm"><i class="pi pi-ellipsis-h"></i></button>
                </div>
                <div class="col-body custom-scroll">
                    <div v-for="w in won" :key="w.id" class="kanban-card card-won">
                        <div class="card-head">
                            <span class="company">{{ w.perusahaan }}</span>
                            <span class="badge-won"><i class="pi pi-star-fill"></i> DEAL</span>
                        </div>
                        <h3 class="contact-name">{{ w.nama }}</h3>
                        <div class="card-foot mt-3">
                            <span class="est-value font-bold text-emerald">{{ formatRupiah(w.estimasi_nilai) }}</span>
                            <button class="btn-action-outline" @click="bukaModalSO(w)">Buat SO / Invoice</button>

                        </div>
                    </div>
                </div>
            </div>

        </div>
    </div>
    <!-- MODAL KONVERSI SALES ORDER -->
    <Dialog v-model:visible="isCreateSOOpen" modal header="Konversi ke Sales Order" :style="{ width: '550px' }"
        class="tech-modal">
        <div class="alert-success-tech mb-4">
            <i class="pi pi-check-circle"></i> Prospek berhasil dikonversi! Lengkapi detail untuk menerbitkan SO.
        </div>

        <form @submit.prevent="handleCreateSO" class="tech-form">
            <div class="input-wrap">
                <label>Nama Pelanggan / Perusahaan</label>
                <input type="text" v-model="formSO.pelanggan" required class="neo-input" readonly>
            </div>

            <div class="form-row">
                <div class="input-wrap">
                    <label>Nilai Penjualan (Rp)</label>
                    <input type="number" v-model="formSO.nilai" required class="neo-input">
                </div>
                <div class="input-wrap">
                    <label>Target Pengiriman</label>
                    <DatePicker v-model="formSO.deadline" dateFormat="dd/mm/yy" placeholder="Pilih tanggal..." fluid
                        :pt="{ input: { class: 'neo-input' } }" />
                </div>
            </div>

            <div class="input-wrap">
                <label>Catatan Operasional</label>
                <textarea v-model="formSO.catatan" rows="3" class="neo-input resize-none"
                    placeholder="Instruksi pengiriman atau terms of payment..."></textarea>
            </div>

            <div class="form-footer">
                <button type="button" @click="isCreateSOOpen = false" class="btn-ghost"
                    :disabled="isConverting">Batal</button>
                <button type="submit" :disabled="isConverting" class="btn-primary-tech">
                    <i v-if="isConverting" class="pi pi-spin pi-spinner"></i>
                    {{ isConverting ? 'Menerbitkan...' : 'Terbitkan SO' }}
                </button>
            </div>
        </form>
    </Dialog>
</template>

<script setup>
// 1. PERBAIKAN IMPORT (Tambahkan ref dan reactive)
import { ref, reactive, onMounted } from 'vue'
import { useCrm } from '@/features/sales/composables/useCrm'

const { isLoading, leads, prospects, won, fetchCrmData, updateLeadStatus } = useCrm()

onMounted(() => {
    fetchCrmData()
})

const formatRupiah = (angka) => {
    return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(angka || 0)
}

const bukaModalProspek = () => {
    alert("Modal tambah prospek (Lead) akan terbuka di sini.")
}

const geserKeNegosiasi = async (id) => {
    await updateLeadStatus(id, 'PROSPECT')
}

const geserKeWon = async (id) => {
    await updateLeadStatus(id, 'WON')
}

// State untuk Modal SO
const isCreateSOOpen = ref(false)
const isConverting = ref(false)

const formSO = reactive({
    prospek_id: null,
    pelanggan: '',
    nilai: null,
    deadline: null,
    catatan: ''
})

// 2. FUNGSI TAMBAHAN YANG TERTINGGAL
const bukaModalSO = (w) => {
    formSO.prospek_id = w.id
    formSO.pelanggan = w.perusahaan
    formSO.nilai = w.estimasi_nilai
    formSO.deadline = null
    formSO.catatan = `[Auto-Generate] Hasil konversi dari prospek: ${w.nama}`

    isCreateSOOpen.value = true
}

const handleCreateSO = async () => {
    isConverting.value = true

    let finalDeadline = formSO.deadline
    if (finalDeadline instanceof Date) {
        finalDeadline = finalDeadline.toISOString().split('T')[0]
    }

    try {
        await new Promise(resolve => setTimeout(resolve, 800))

        alert(`Sales Order untuk ${formSO.pelanggan} senilai ${formatRupiah(formSO.nilai)} berhasil diterbitkan!`)
        isCreateSOOpen.value = false

    } catch (error) {
        alert("Gagal menerbitkan Sales Order.")
    } finally {
        isConverting.value = false
    }
}
</script>

<style scoped>
* {
    box-sizing: border-box;
}

.crm-dashboard {
    padding: 2rem;
    max-width: 1600px;
    /* Lebih lebar untuk Kanban */
    margin: 0 auto;
    font-family: 'Inter', -apple-system, sans-serif;
    color: #0f172a;
    height: 100vh;
    display: flex;
    flex-direction: column;
}

/* HEADER */
.tech-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
}

.title-wrapper {
    display: flex;
    align-items: center;
    gap: 1rem;
}

.title-icon {
    width: 3rem;
    height: 3rem;
    background: linear-gradient(135deg, #0f172a, #1e293b);
    color: #14b8a6;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.25rem;
    box-shadow: 0 4px 12px rgba(15, 23, 42, 0.15);
}

.tech-header h1 {
    font-size: 1.5rem;
    font-weight: 800;
    margin: 0 0 0.25rem 0;
    letter-spacing: -0.03em;
}

.tech-header p {
    font-size: 0.875rem;
    color: #64748b;
    margin: 0;
}

.header-actions {
    display: flex;
    gap: 1rem;
    align-items: center;
}

.search-bar {
    position: relative;
}

.search-bar i {
    position: absolute;
    left: 1rem;
    top: 50%;
    transform: translateY(-50%);
    color: #94a3b8;
}

.search-input {
    width: 300px;
    padding-left: 2.5rem !important;
    border-radius: 99px !important;
}

.btn-primary-tech {
    background: linear-gradient(180deg, #0d9488 0%, #0f766e 100%);
    color: #fff;
    border: 1px solid #115e59;
    padding: 0.6rem 1.25rem;
    border-radius: 99px;
    font-weight: 600;
    font-size: 0.875rem;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    box-shadow: 0 2px 4px rgba(13, 148, 136, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.1);
    transition: all 0.2s;
}

.btn-primary-tech:hover {
    background: linear-gradient(180deg, #14b8a6 0%, #0d9488 100%);
    transform: translateY(-1px);
    box-shadow: 0 4px 10px rgba(13, 148, 136, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

.neo-input {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    padding: 0.6rem 1rem;
    font-size: 0.875rem;
    color: #0f172a;
    transition: all 0.2s;
    font-family: inherit;
}

.neo-input:focus {
    outline: none;
    border-color: #14b8a6;
    box-shadow: 0 0 0 3px rgba(20, 184, 166, 0.1);
}

/* TABS NAVIGATION */
.crm-tabs {
    display: flex;
    gap: 0.5rem;
    border-bottom: 2px solid #e2e8f0;
    margin-bottom: 1.5rem;
}

.tab-btn {
    background: transparent;
    border: none;
    padding: 0.75rem 1.25rem;
    font-size: 0.875rem;
    font-weight: 600;
    color: #64748b;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    border-bottom: 2px solid transparent;
    margin-bottom: -2px;
    transition: 0.2s;
}

.tab-btn:hover {
    color: #0f172a;
}

.tab-btn.active {
    color: #0d9488;
    border-bottom-color: #0d9488;
}

/* KANBAN BOARD */
.kanban-board {
    display: flex;
    gap: 1.5rem;
    flex: 1;
    overflow-x: auto;
    padding-bottom: 1rem;
}

.kanban-col {
    flex: 0 0 350px;
    /* Fixed width untuk tiap kolom */
    background: #f1f5f9;
    border-radius: 12px;
    display: flex;
    flex-direction: column;
    max-height: 100%;
    border: 1px solid #e2e8f0;
}

/* Column Header */
.col-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 1.25rem;
    border-bottom: 1px solid #e2e8f0;
}

.col-title {
    font-size: 0.8125rem;
    font-weight: 800;
    color: #334155;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
}

.dot-new {
    background: #3b82f6;
    box-shadow: 0 0 8px #3b82f6;
}

.dot-nego {
    background: #f59e0b;
    box-shadow: 0 0 8px #f59e0b;
}

.dot-won {
    background: #10b981;
    box-shadow: 0 0 8px #10b981;
}

.count {
    background: #e2e8f0;
    padding: 0.1rem 0.5rem;
    border-radius: 99px;
    font-size: 0.7rem;
    color: #475569;
}

.btn-icon-sm {
    background: transparent;
    border: none;
    color: #94a3b8;
    cursor: pointer;
    transition: 0.2s;
}

.btn-icon-sm:hover {
    color: #0f172a;
}

/* Column Body */
.col-body {
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
    overflow-y: auto;
    flex: 1;
}

/* KANBAN CARDS */
.kanban-card {
    background: #ffffff;
    border-radius: 10px;
    padding: 1.25rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    border: 1px solid #e2e8f0;
    cursor: grab;
    transition: transform 0.2s, box-shadow 0.2s;
}

.kanban-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 12px rgba(0, 0, 0, 0.08);
    border-color: #cbd5e1;
}

.kanban-card:active {
    cursor: grabbing;
}

.border-nego {
    border-left: 4px solid #f59e0b;
}

.card-won {
    background: linear-gradient(to bottom right, #ffffff, #f0fdf4);
    border: 1px solid #bbf7d0;
}

.card-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
    font-size: 0.75rem;
}

.company {
    font-weight: 700;
    color: #0d9488;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.date {
    color: #94a3b8;
    font-weight: 500;
}

.text-warn {
    color: #d97706;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 0.3rem;
}

.contact-name {
    font-size: 1.125rem;
    font-weight: 800;
    margin: 0 0 0.5rem 0;
    color: #0f172a;
}

.contact-info {
    font-size: 0.8125rem;
    color: #475569;
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
    margin-bottom: 1rem;
}

.contact-info i {
    color: #10b981;
}

.progress-bar {
    height: 6px;
    background: #f1f5f9;
    border-radius: 99px;
    overflow: hidden;
    margin-bottom: 1rem;
}

.progress-fill {
    height: 100%;
    background: #f59e0b;
    border-radius: 99px;
}

.card-foot {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-top: 1px dashed #e2e8f0;
    padding-top: 1rem;
}

.mt-3 {
    margin-top: 1rem;
}

.est-value {
    font-size: 0.875rem;
    font-weight: 600;
    color: #64748b;
}

.est-value.highlight {
    color: #0f172a;
    font-weight: 800;
}

.font-bold {
    font-weight: 800;
}

.text-emerald {
    color: #047857;
}

.badge-won {
    background: #10b981;
    color: white;
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    font-weight: 800;
    display: flex;
    align-items: center;
    gap: 0.2rem;
}

/* Action Buttons inside Card */
.btn-move {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    color: #334155;
    padding: 0.3rem 0.6rem;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 700;
    cursor: pointer;
    transition: 0.2s;
    display: flex;
    align-items: center;
    gap: 0.3rem;
}

.btn-move:hover {
    background: #0f172a;
    color: #fff;
    border-color: #0f172a;
}

.btn-move.success:hover {
    background: #10b981;
    border-color: #10b981;
    color: white;
}

.btn-action-outline {
    width: 100%;
    background: transparent;
    border: 1px solid #0d9488;
    color: #0d9488;
    padding: 0.5rem;
    border-radius: 6px;
    font-weight: 700;
    cursor: pointer;
    transition: 0.2s;
}

.btn-action-outline:hover {
    background: #0d9488;
    color: white;
}

/* Custom Scrollbar */
.custom-scroll::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}

.custom-scroll::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 10px;
}

.animate-fade-in {
    animation: fadeIn 0.4s ease-out forwards;
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