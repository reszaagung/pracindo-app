<template>
    <div class="tech-card">
        <div class="card-indicator" :class="'ind-' + wo.kategori.toLowerCase()"></div>
        <div class="card-inner">
            <div class="card-top">
                <span class="tech-badge" :class="'badge-' + wo.kategori.toLowerCase()">
                    <span class="dot"></span> {{ wo.kategori }}
                </span>
                <span class="tech-id">#{{ wo.nomor }}</span>
            </div>
            <div class="card-body">
                <h3 class="judul">{{ wo.judul }}</h3>
                <p class="deskripsi">{{ wo.deskripsi }}</p>
                <div class="assignment-panel">
                    <div class="assign-item">
                        <i class="pi pi-user-edit"></i>
                        <div class="assign-text">
                            <span class="lbl">Diberikan Oleh</span>
                            <span class="val">{{ wo.dibuat_oleh_nama || 'Sistem' }}</span>
                        </div>
                    </div>
                    <div class="assign-item">
                        <i class="pi pi-users"></i>
                        <div class="assign-text">
                            <span class="lbl">Ditugaskan Kepada</span>
                            <div class="tag-list">
                                <span v-for="tag in wo.penugasan" :key="tag.id" class="name-badge"
                                    :class="{ 'is-pic': tag.is_pic }">
                                    {{ tag.staff_nama }}
                                    <i v-if="tag.is_pic" class="pi pi-star-fill star-icon" title="PIC Utama"></i>
                                </span>
                                <span v-if="!wo.penugasan || wo.penugasan.length === 0" class="val text-muted">
                                    Belum ada staf yang di-tag
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
                <div v-if="wo.kategori === 'PRODUKSI' && wo.detail_produksi" class="specs-panel">
                    <div class="specs-header">
                        <i class="pi pi-cog"></i> PARAMETER MANUFAKTUR
                    </div>
                    <div class="specs-grid">
                        <div class="spec-item">
                            <span class="lbl">VARIAN</span>
                            <span class="val">{{ wo.detail_produksi.nama_item }}</span>
                        </div>
                        <div class="spec-item">
                            <span class="lbl">KEMASAN</span>
                            <span class="val">{{ wo.detail_produksi.unit_display }}</span>
                        </div>
                        <div class="spec-item full">
                            <span class="lbl">STIKER</span>
                            <span class="val">{{ wo.detail_produksi.stiker_display }}</span>
                        </div>
                    </div>
                </div>
            </div>
            <div class="card-footer">
                <div class="meta-info">
                    <i class="pi pi-clock"></i>
                    <span :class="{ 'text-danger': wo.terlambat }">
                        {{ wo.deadline || 'Tanpa Tenggat' }}
                    </span>
                </div>
            </div>
            <div class="card-actions">
                <button class="btn-action chat" @click="$emit('open-chat', wo)">
                    <i class="pi pi-comments"></i>
                    <span class="count" v-if="wo.jumlah_pesan">{{ wo.jumlah_pesan }}</span>
                </button>

                <!-- Jika yang login adalah pembuat tugas -->
                <button v-if="wo.dibuat_oleh === currentUserId"
                    class="btn-action close-session"
                    @click="$emit('close-session', wo)"
                    title="Tutup Sesi (Sembunyikan dari Mading)">
                    <i class="pi pi-power-off"></i> Tutup Sesi
                </button>

                <!-- Jika yang login adalah penerima tugas (PIC) -->
                <button v-else
                    class="btn-action complete"
                    @click="$emit('approve', wo)"
                    title="Tandai Selesai">
                    <i class="pi pi-check"></i> Selesaikan
                </button>
            </div>
        </div>
    </div>
</template>

<script setup>
const props = defineProps({
    wo: {
        type: Object,
        required: true
    },
    currentUserId: {
        type: [Number, String],
        required: true
    }
})

defineEmits(['open-chat', 'approve', 'close-session'])
</script>

<style scoped>
.tech-card {
    background: #ffffff;
    border: 1px solid rgba(226, 232, 240, 0.8);
    border-radius: 12px;
    position: relative;
    display: flex;
    flex-direction: column;
    box-shadow: 0 2px 4px rgba(15, 23, 42, 0.02), 0 1px 2px rgba(15, 23, 42, 0.03);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.tech-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 20px -8px rgba(15, 23, 42, 0.1), 0 4px 6px -3px rgba(15, 23, 42, 0.05);
    border-color: #cbd5e1;
}

.card-indicator {
    height: 4px;
    width: 100%;
    border-radius: 12px 12px 0 0;
}

.ind-produksi { background: linear-gradient(90deg, #f43f5e, #fb7185); }
.ind-gudang { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
.ind-umum { background: linear-gradient(90deg, #3b82f6, #60a5fa); }

.card-inner {
    padding: 1.25rem;
    display: flex;
    flex-direction: column;
    flex: 1;
}

.card-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
}

.tech-badge {
    font-size: 0.65rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 0.25rem 0.6rem;
    border-radius: 999px;
    display: flex;
    align-items: center;
    gap: 0.3rem;
}

.tech-badge .dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
}

.badge-produksi { background: #fff1f2; color: #be123c; border: 1px solid #ffe4e6; }
.badge-produksi .dot { background: #e11d48; }
.badge-gudang { background: #fffbeb; color: #b45309; border: 1px solid #fef3c7; }
.badge-gudang .dot { background: #d97706; }
.badge-umum { background: #eff6ff; color: #1d4ed8; border: 1px solid #dbeafe; }
.badge-umum .dot { background: #2563eb; }

.tech-id {
    font-family: 'Courier New', Courier, monospace;
    font-size: 0.75rem;
    color: #94a3b8;
    font-weight: 600;
}

.card-body {
    flex: 1;
    margin-bottom: 1.5rem;
}

.judul {
    font-size: 1.0625rem;
    font-weight: 700;
    color: #0f172a;
    margin: 0 0 0.35rem 0;
    line-height: 1.4;
}

.deskripsi {
    font-size: 0.875rem;
    color: #64748b;
    margin: 0;
    line-height: 1.5;
}

.assignment-panel {
    margin-top: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.85rem;
    background: #f8fafc;
    border: 1px dashed #cbd5e1;
    padding: 0.85rem;
    border-radius: 8px;
}

.assign-item {
    display: flex;
    align-items: flex-start;
    gap: 0.6rem;
}

.assign-item i {
    font-size: 0.875rem;
    color: #64748b;
    margin-top: 0.15rem;
}

.assign-text {
    display: flex;
    flex-direction: column;
    gap: 0.15rem;
}

.assign-text .lbl {
    font-size: 0.65rem;
    color: #64748b;
    text-transform: uppercase;
    font-weight: 700;
    letter-spacing: 0.05em;
}

.assign-text .val {
    font-size: 0.8125rem;
    color: #0f172a;
    font-weight: 600;
}

.assign-text .text-muted {
    color: #94a3b8;
    font-weight: 500;
    font-style: italic;
}

.tag-list {
    display: flex;
    flex-wrap: wrap;
    gap: 0.35rem;
    margin-top: 0.2rem;
}

.name-badge {
    font-size: 0.7rem;
    background: #e2e8f0;
    color: #334155;
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    font-weight: 600;
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
}

.name-badge.is-pic {
    background: #ccfbf1;
    color: #0f766e;
    border: 1px solid #99f6e4;
}

.star-icon {
    font-size: 0.55rem;
    color: #0d9488 !important;
}

.specs-panel {
    margin-top: 1rem;
    background: #0f172a;
    border-radius: 8px;
    padding: 0.75rem;
    border: 1px solid #1e293b;
}

.specs-header {
    font-size: 0.625rem;
    font-family: monospace;
    color: #14b8a6;
    font-weight: 700;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    gap: 0.3rem;
}

.specs-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
}

.spec-item {
    display: flex;
    flex-direction: column;
    width: calc(50% - 0.25rem);
}

.spec-item.full {
    width: 100%;
}

.spec-item .lbl {
    font-size: 0.55rem;
    color: #64748b;
    letter-spacing: 0.05em;
    margin-bottom: 0.1rem;
}

.spec-item .val {
    font-size: 0.75rem;
    color: #f8fafc;
    font-weight: 600;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.card-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 1rem;
    border-bottom: 1px dashed #e2e8f0;
    margin-bottom: 1rem;
}

.meta-info {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.75rem;
    color: #64748b;
    font-weight: 500;
}

.text-danger {
    color: #e11d48;
    font-weight: 700;
}

.card-actions {
    display: flex;
    gap: 0.5rem;
}

.btn-action {
    flex: 1;
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 0.4rem;
    padding: 0.5rem;
    border-radius: 6px;
    font-size: 0.8125rem;
    font-weight: 600;
    cursor: pointer;
    transition: 0.2s;
    border: none;
}

.btn-action.chat {
    background: #f8fafc;
    color: #475569;
    border: 1px solid #e2e8f0;
}

.btn-action.chat:hover {
    background: #f1f5f9;
    color: #0f172a;
}

.btn-action.chat .count {
    background: #e2e8f0;
    padding: 0.1rem 0.4rem;
    border-radius: 99px;
    font-size: 0.65rem;
}

.btn-action.complete {
    background: #f0fdf4;
    color: #166534;
    border: 1px solid #bbf7d0;
}

.btn-action.complete:hover {
    background: #dcfce7;
    color: #14532d;
    border-color: #86efac;
}

.btn-action.close-session {
    background: #fff1f2;
    color: #e11d48;
    border: 1px solid #fecdd3;
}

.btn-action.close-session:hover {
    background: #ffe4e6;
    color: #be123c;
    border-color: #fda4af;
}
</style>
