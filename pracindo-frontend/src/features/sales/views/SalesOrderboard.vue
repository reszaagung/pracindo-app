<!-- src/views/sales/SalesOrderBoard.vue -->
<template>
    <div class="sales-board animate-fade-in">
        <!-- HEADER -->
        <header class="tech-header">
            <div class="title-wrapper">
                <div class="title-icon">
                    <i class="pi pi-chart-line"></i>
                </div>
                <div>
                    <h1>Portal Sales & Distribusi</h1>
                    <p>Kelola pesanan pelanggan, target omset, dan pelacakan pengiriman.</p>
                </div>
            </div>

            <div class="header-actions">
                <button @click="bukaModalBuat" class="btn-primary-tech">
                    <i class="pi pi-plus"></i> <span>Buat Pesanan (SO)</span>
                </button>
                <button @click="fetchSalesOrders" class="btn-icon-tech" aria-label="Refresh">
                    <i class="pi pi-refresh" :class="{ 'pi-spin': isLoading }"></i>
                </button>
            </div>
        </header>

        <!-- STATISTIK (Metric Cards) -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon bg-teal"><i class="pi pi-wallet"></i></div>
                <div class="stat-data">
                    <span class="stat-label">Total Omset Berjalan</span>
                    <span class="stat-value">{{ formatRupiah(statistik.total_omset) }}</span>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon bg-blue"><i class="pi pi-shopping-cart"></i></div>
                <div class="stat-data">
                    <span class="stat-label">Pesanan Aktif</span>
                    <span class="stat-value">{{ statistik.pesanan_aktif }} <small>Dokumen</small></span>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon bg-emerald"><i class="pi pi-check-circle"></i></div>
                <div class="stat-data">
                    <span class="stat-label">Pesanan Selesai</span>
                    <span class="stat-value">{{ statistik.pesanan_selesai }} <small>Dokumen</small></span>
                </div>
            </div>
        </div>

        <!-- LIST PESANAN (Sales Orders) -->
        <div class="list-container">
            <div class="list-header">
                <h2>Daftar Sales Order (SO)</h2>
                <div class="list-filters">
                    <span class="p-input-icon-left">
                        <i class="pi pi-search" />
                        <input type="text" class="neo-input search-input" placeholder="Cari SO atau Pelanggan..." />
                    </span>
                </div>
            </div>

            <div v-if="isLoading" class="tech-loading">
                <div class="loader-pulse"></div>
            </div>

            <div v-else-if="salesOrders.length === 0" class="tech-empty">
                <i class="pi pi-folder-open"></i>
                <p>Belum ada transaksi penjualan yang tercatat.</p>
            </div>

            <div v-else class="so-list">
                <div v-for="so in salesOrders" :key="so.id" class="so-item">
                    <div class="so-main">
                        <div class="so-id">{{ so.nomor || 'SO-PENDING' }}</div>
                        <div class="so-customer">{{ so.pelanggan }}</div>
                    </div>

                    <div class="so-details">
                        <div class="so-date">
                            <span class="lbl">TANGGAL SO</span>
                            <span class="val">{{ formatDate(so.tanggal || so.created_at) }}</span>
                        </div>
                        <div class="so-date">
                            <span class="lbl">TARGET KIRIM</span>
                            <span class="val">{{ formatDate(so.deadline) }}</span>
                        </div>
                        <div class="so-amount">
                            <span class="lbl">NILAI PESANAN</span>
                            <span class="val highlight">{{ formatRupiah(so.nilai) }}</span>
                        </div>
                    </div>

                    <div class="so-status">
                        <span class="tech-badge" :class="'status-' + (so.status || 'DRAFT').toLowerCase()">
                            {{ formatStatus(so.status || 'DRAFT') }}
                        </span>
                    </div>

                    <div class="so-actions">
                        <button class="btn-action-sm" v-tooltip.top="'Lihat Detail'"><i
                                class="pi pi-external-link"></i></button>
                    </div>
                </div>
            </div>
        </div>

        <!-- MODAL BUAT SO BARU -->
        <Dialog v-model:visible="isCreateOpen" modal header="Buat Sales Order Baru" :style="{ width: '550px' }"
            class="tech-modal">
            <form @submit.prevent="handleCreate" class="tech-form">
                <div class="input-wrap">
                    <label>Nama Pelanggan / Perusahaan</label>
                    <input type="text" v-model="formCreate.pelanggan" required class="neo-input"
                        placeholder="Contoh: PT. Makmur Sentosa">
                </div>

                <div class="form-row">
                    <div class="input-wrap">
                        <label>Estimasi Nilai (Rp)</label>
                        <input type="number" v-model="formCreate.nilai" required class="neo-input" placeholder="0">
                    </div>
                    <div class="input-wrap">
                        <label>Target Pengiriman</label>
                        <DatePicker v-model="formCreate.deadline" dateFormat="dd/mm/yy" placeholder="Pilih tanggal..."
                            fluid :pt="{ input: { class: 'neo-input' } }" />
                    </div>
                </div>

                <div class="input-wrap">
                    <label>Catatan Pesanan</label>
                    <textarea v-model="formCreate.catatan" rows="3" class="neo-input resize-none"
                        placeholder="Instruksi pengiriman, terms of payment, dll..."></textarea>
                </div>

                <div class="form-footer">
                    <button type="button" @click="isCreateOpen = false" class="btn-ghost"
                        :disabled="isCreating">Batal</button>
                    <button type="submit" :disabled="isCreating" class="btn-primary-tech">
                        <i v-if="isCreating" class="pi pi-spin pi-spinner"></i>
                        {{ isCreating ? 'Menyimpan...' : 'Terbitkan SO' }}
                    </button>
                </div>
            </form>
        </Dialog>
    </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useSales } from '@/features/sales/composables/useSales'
import Dialog from 'primevue/dialog'
import DatePicker from 'primevue/datepicker'

const { isLoading, isCreating, salesOrders, statistik, fetchSalesOrders, createSalesOrder } = useSales()

const isCreateOpen = ref(false)
const formCreate = reactive({
    pelanggan: '',
    nilai: null,
    deadline: null,
    catatan: ''
})

onMounted(() => {
    fetchSalesOrders()
})

const bukaModalBuat = () => {
    Object.assign(formCreate, { pelanggan: '', nilai: null, deadline: null, catatan: '' })
    isCreateOpen.value = true
}

const handleCreate = async () => {
    const payload = { ...formCreate }

    // Format DatePicker ke ISO String untuk backend
    if (payload.deadline instanceof Date) {
        payload.deadline = payload.deadline.toISOString().split('T')[0] // Format YYYY-MM-DD
    } else if (!payload.deadline) {
        delete payload.deadline
    }

    const res = await createSalesOrder(payload)
    if (res.success) {
        isCreateOpen.value = false
    } else {
        alert(`Gagal: ${res.message}`)
    }
}

// Utilities Formatting
const formatRupiah = (angka) => {
    return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(angka || 0)
}

const formatDate = (dateString) => {
    if (!dateString) return '-'
    const options = { day: 'numeric', month: 'short', year: 'numeric' }
    return new Date(dateString).toLocaleDateString('id-ID', options)
}

const formatStatus = (status) => {
    return status.replace('_', ' ')
}
</script>

<style scoped>
* {
    box-sizing: border-box;
}

.sales-board {
    padding: 2rem;
    max-width: 1440px;
    margin: 0 auto;
    font-family: 'Inter', -apple-system, sans-serif;
    color: #0f172a;
}

/* HEADER */
.tech-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid rgba(226, 232, 240, 0.8);
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
    gap: 0.75rem;
}

.btn-primary-tech {
    background: linear-gradient(180deg, #0d9488 0%, #0f766e 100%);
    color: #fff;
    border: 1px solid #115e59;
    padding: 0.6rem 1.2rem;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.875rem;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    box-shadow: 0 2px 4px rgba(13, 148, 136, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.1);
    transition: all 0.2s;
}

.btn-primary-tech:hover:not(:disabled) {
    background: linear-gradient(180deg, #14b8a6 0%, #0d9488 100%);
    transform: translateY(-1px);
    box-shadow: 0 4px 10px rgba(13, 148, 136, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

.btn-icon-tech {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    color: #475569;
    padding: 0.6rem 0.8rem;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
}

.btn-icon-tech:hover {
    background: #f8fafc;
    color: #0f172a;
    border-color: #cbd5e1;
}

/* STATISTIK CARDS */
.stats-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1.5rem;
    margin-bottom: 2.5rem;
}

.stat-card {
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1.5rem;
    display: flex;
    align-items: center;
    gap: 1.25rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
    transition: transform 0.2s;
}

.stat-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.stat-icon {
    width: 3.5rem;
    height: 3.5rem;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
    color: #fff;
}

.bg-teal {
    background: #0d9488;
}

.bg-blue {
    background: #2563eb;
}

.bg-emerald {
    background: #10b981;
}

.stat-data {
    display: flex;
    flex-direction: column;
}

.stat-label {
    font-size: 0.75rem;
    font-weight: 700;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.25rem;
}

.stat-value {
    font-size: 1.5rem;
    font-weight: 800;
    color: #0f172a;
    letter-spacing: -0.02em;
}

.stat-value small {
    font-size: 0.875rem;
    color: #94a3b8;
    font-weight: 500;
}

/* LIST PESANAN */
.list-container {
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    overflow: hidden;
}

.list-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.25rem 1.5rem;
    border-bottom: 1px solid #e2e8f0;
    background: #f8fafc;
}

.list-header h2 {
    font-size: 1.125rem;
    font-weight: 700;
    margin: 0;
    color: #1e293b;
}

.search-input {
    width: 250px;
    padding-left: 2.5rem !important;
}

/* LIST ITEMS */
.so-list {
    display: flex;
    flex-direction: column;
}

.so-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1.25rem 1.5rem;
    border-bottom: 1px solid #f1f5f9;
    transition: background 0.2s;
}

.so-item:hover {
    background: #f8fafc;
}

.so-item:last-child {
    border-bottom: none;
}

.so-main {
    flex: 0 0 25%;
}

.so-id {
    font-family: monospace;
    font-size: 0.875rem;
    font-weight: 700;
    color: #0d9488;
    margin-bottom: 0.25rem;
}

.so-customer {
    font-size: 1rem;
    font-weight: 700;
    color: #0f172a;
}

.so-details {
    display: flex;
    flex: 1;
    justify-content: space-around;
    padding: 0 1rem;
}

.so-date,
.so-amount {
    display: flex;
    flex-direction: column;
}

.lbl {
    font-size: 0.65rem;
    font-weight: 700;
    color: #94a3b8;
    letter-spacing: 0.05em;
    margin-bottom: 0.25rem;
}

.val {
    font-size: 0.875rem;
    color: #334155;
    font-weight: 500;
}

.val.highlight {
    font-weight: 700;
    color: #0f172a;
}

.so-status {
    flex: 0 0 15%;
    display: flex;
    justify-content: center;
}

.tech-badge {
    font-size: 0.7rem;
    font-weight: 700;
    padding: 0.35rem 0.75rem;
    border-radius: 6px;
}

.status-draft {
    background: #f1f5f9;
    color: #475569;
    border: 1px solid #cbd5e1;
}

.status-diproses {
    background: #fffbeb;
    color: #b45309;
    border: 1px solid #fde68a;
}

.status-siap_kirim {
    background: #eff6ff;
    color: #1d4ed8;
    border: 1px solid #bfdbfe;
}

.status-selesai {
    background: #ecfdf5;
    color: #047857;
    border: 1px solid #a7f3d0;
}

.so-actions {
    flex: 0 0 5%;
    display: flex;
    justify-content: flex-end;
}

.btn-action-sm {
    background: transparent;
    border: 1px solid transparent;
    color: #94a3b8;
    width: 2rem;
    height: 2rem;
    border-radius: 6px;
    cursor: pointer;
    transition: 0.2s;
}

.btn-action-sm:hover {
    background: #f1f5f9;
    color: #0f172a;
    border-color: #cbd5e1;
}

/* LOADING & EMPTY */
.tech-loading,
.tech-empty {
    padding: 4rem 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    color: #94a3b8;
}

.tech-empty i {
    font-size: 2.5rem;
    margin-bottom: 1rem;
    color: #cbd5e1;
}

.loader-pulse {
    width: 2rem;
    height: 2rem;
    border-radius: 50%;
    background: #14b8a6;
    animation: pulse-glow 1.5s infinite;
}

@keyframes pulse-glow {
    0% {
        transform: scale(0.9);
        box-shadow: 0 0 0 0 rgba(20, 184, 166, 0.5);
    }

    70% {
        transform: scale(1);
        box-shadow: 0 0 0 15px rgba(20, 184, 166, 0);
    }

    100% {
        transform: scale(0.9);
        box-shadow: 0 0 0 0 rgba(20, 184, 166, 0);
    }
}

/* MODAL & FORMS */
:deep(.tech-modal .p-dialog-header) {
    background: #ffffff;
    border-bottom: 1px solid #f1f5f9;
    padding: 1.25rem 1.5rem;
}

:deep(.tech-modal .p-dialog-title) {
    font-weight: 700;
    font-size: 1.125rem;
    color: #0f172a;
}

:deep(.tech-modal .p-dialog-content) {
    padding: 1.5rem;
    background: #fafaf9;
}

.tech-form {
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
    font-family: inherit;
}

.form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
}

.input-wrap label {
    display: block;
    font-size: 0.75rem;
    font-weight: 700;
    color: #475569;
    text-transform: uppercase;
    margin-bottom: 0.4rem;
    letter-spacing: 0.05em;
}

.neo-input {
    width: 100%;
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
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

.resize-none {
    resize: none;
}

.form-footer {
    display: flex;
    justify-content: flex-end;
    gap: 0.75rem;
    margin-top: 0.5rem;
}

.btn-ghost {
    background: transparent;
    color: #64748b;
    font-weight: 600;
    font-size: 0.875rem;
    border: none;
    padding: 0.6rem 1rem;
    border-radius: 8px;
    cursor: pointer;
}

.btn-ghost:hover {
    background: #e2e8f0;
    color: #0f172a;
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

@media (max-width: 1024px) {
    .stats-grid {
        grid-template-columns: 1fr;
    }

    .so-item {
        flex-direction: column;
        align-items: flex-start;
        gap: 1rem;
    }

    .so-main,
    .so-details,
    .so-status,
    .so-actions {
        flex: 1;
        width: 100%;
        justify-content: flex-start;
        padding: 0;
    }

    .so-details {
        flex-wrap: wrap;
        gap: 1rem;
    }
}
</style>