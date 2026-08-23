<template>
    <div class="wo-board animate-fade-in">
        <header :class="['flex justify-between gap-4 mb-8 pb-6 border-b border-slate-200', isMobile ? 'flex-col' : 'flex-row items-center']">
            <div class="flex items-center gap-4">
                <div :class="['bg-slate-900 rounded-xl flex items-center justify-center shrink-0 shadow-sm', isMobile ? 'w-10 h-10' : 'w-12 h-12']">
                    <i :class="['pi pi-desktop text-teal-400', isMobile ? 'text-lg' : 'text-xl']"></i>
                </div>
                <div class="flex flex-col">
                    <h1 :class="['font-black text-slate-900 leading-tight m-0 tracking-tight', isMobile ? 'text-2xl' : 'text-3xl']">
                        Mading Operasional
                    </h1>
                    <p :class="['text-slate-500 mt-1 m-0', isMobile ? 'text-xs' : 'text-sm']">
                        Kontrol pusat pesanan pabrik dan penugasan tim.
                    </p>
                </div>
            </div>
            <div :class="['flex gap-3', isMobile ? 'w-full' : 'w-auto']">
                <button @click="bukaModalBuat" class="btn-primary-tech" :class="isMobile ? 'flex-1 justify-center' : ''">
                    <i class="pi pi-plus"></i> <span>{{ isMobile ? 'Tugas Baru' : 'Buat Tugas Baru' }}</span>
                </button>
                <button @click="fetchMading" class="btn-icon-tech shrink-0" aria-label="Refresh">
                    <i class="pi pi-refresh" :class="{ 'pi-spin': isLoading }"></i>
                </button>
            </div>
        </header>

        <div v-if="isLoading && madingList.length === 0" class="wo-loading">
            <div class="loader-pulse"></div>
            <p>Sinkronisasi data...</p>
        </div>

        <div v-else-if="!isLoading && madingList.length === 0" class="wo-empty">
            <div class="empty-glow">
                <i class="pi pi-check-circle"></i>
            </div>
            <h3>Panel Tugas</h3>
            <p>Tidak ada antrean pesanan atau tugas aktif. Ruang kerja bersih!</p>
        </div>

        <div v-else class="wo-grid" :data-count="madingList.length > 4 ? 'more' : madingList.length">
            <PostWorkOrderCard v-for="wo in madingList" :key="wo.id" :wo="wo" :currentUserId="currentUserId"
                @open-chat="openChatModal" @approve="handleApprove" />
        </div>

        <Dialog v-model:visible="isCreateOpen" modal header="Inisiasi Tugas Baru" :style="{ width: '500px' }"
            class="tech-modal">
            <form @submit.prevent="handleCreate" class="tech-form">
                <div class="form-row">
                    <div class="input-wrap">
                        <label>Target Penerima Tugas (PIC)</label>
                        <MultiSelect v-model="formCreate.staff_ids" :options="staffList" optionLabel="nama_lengkap"
                            optionValue="id" placeholder="Pilih pelaksana..." display="chip" fluid />
                    </div>
                    <div class="input-wrap">
                        <label>Tenggat Waktu</label>
                        <DatePicker v-model="formCreate.deadline" showTime hourFormat="24" dateFormat="dd/mm/yy"
                            placeholder="Pilih tanggal & jam..." fluid :pt="{
                                input: { class: 'neo-input' }
                            }" />
                    </div>
                </div>
                <div class="input-wrap">
                    <label>Target Penerima Tugas (PIC)</label>
                    <MultiSelect v-model="formCreate.staff_ids" :options="staffTanpaPembuat" optionLabel="nama_lengkap"
                        optionValue="id" placeholder="Pilih pelaksana..." display="chip" fluid />
                </div>
                <div class="input-wrap">
                    <label>Identifikasi Tugas</label>
                    <input type="text" v-model="formCreate.judul" required class="neo-input"
                        placeholder="Masukkan judul spesifik...">
                </div>
                <div class="input-wrap">
                    <label>Parameter Detail</label>
                    <textarea v-model="formCreate.deskripsi" rows="4" class="neo-input resize-none"
                        placeholder="Uraikan instruksi pekerjaan di sini..."></textarea>
                </div>
                <div class="form-footer">
                    <button type="button" @click="isCreateOpen = false" class="btn-ghost"
                        :disabled="isCreating">Batalkan</button>
                    <button type="submit" :disabled="isCreating" class="btn-primary-tech">
                        <i v-if="isCreating" class="pi pi-spin pi-spinner"></i>
                        {{ isCreating ? 'Memproses...' : 'Eksekusi Tugas' }}
                    </button>
                </div>
            </form>
        </Dialog>

        <Dialog v-model:visible="isChatOpen" modal header="Terminal Diskusi" :style="{ width: '450px' }"
            class="tech-modal">
            <div v-if="activeWO" class="chat-wrapper">
                <div class="chat-feed custom-scroll" ref="chatBox">
                    <div v-if="activeWO.pesan_chat.length === 0" class="chat-blank">
                        <i class="pi pi-wave-pulse"></i>
                        <p>Saluran komunikasi terbuka. Belum ada aktivitas.</p>
                    </div>
                    <div v-for="msg in activeWO.pesan_chat" :key="msg.id" class="message-block">
                        <span class="sender-id">{{ msg.pengirim_nama }}</span>
                        <div class="message-core">
                            {{ msg.teks }}
                        </div>
                    </div>
                </div>
                <div class="chat-control">
                    <input type="text" v-model="chatInput" @keyup.enter="kirimPesan" placeholder="Transmisikan pesan..."
                        class="neo-input">
                    <button @click="kirimPesan" :disabled="isSending || !chatInput.trim()" class="btn-send-tech">
                        <i class="pi pi-send" :class="{ 'pi-spin pi-spinner': isSending }"></i>
                    </button>
                </div>
            </div>
        </Dialog>
    </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick, computed } from 'vue'
import { useWorkOrder } from '@/features/work-order/composables/useWorkOrder'
import Dialog from 'primevue/dialog'
import DatePicker from 'primevue/datepicker'
import MultiSelect from 'primevue/multiselect'
import PostWorkOrderCard from '../components/PostWorkOrderCard.vue'
import { useDevice } from '@/composables/useDevice'

const { isMobile } = useDevice()

const {
    isLoading, isSending, isCreating, isChatLoading,
    madingList, staffList, fetchMading, fetchStaff,
    approveTask, sendReply, createTask, fetchChat
} = useWorkOrder()

const currentUserId = ref(1)

const staffTanpaPembuat = computed(() => {
    return staffList.value.filter(staff => staff.id !== currentUserId.value)
})

const isChatOpen = ref(false)
const isCreateOpen = ref(false)
const activeWO = ref(null)
const chatInput = ref('')
const chatBox = ref(null)

const formCreate = reactive({
    judul: '',
    deskripsi: '',
    kategori: 'UMUM',
    deadline: '',
    staff_ids: []
})

onMounted(() => {
    fetchMading()
    fetchStaff()
})

const bukaModalBuat = () => {
    Object.assign(formCreate, {
        judul: '', deskripsi: '', kategori: 'UMUM', deadline: '', staff_ids: []
    })
    isCreateOpen.value = true
}

const handleCreate = async () => {
    const payload = { ...formCreate }
    if (!payload.deadline) {
        delete payload.deadline
    } else if (payload.deadline instanceof Date) {
        const year = payload.deadline.getFullYear();
        const month = String(payload.deadline.getMonth() + 1).padStart(2, '0');
        const day = String(payload.deadline.getDate()).padStart(2, '0');
        payload.deadline = `${year}-${month}-${day}`;
    }
    const res = await createTask(payload)
    if (res.success) {
        isCreateOpen.value = false
    } else {
        alert(`Gagal: ${res.message}`)
    }
}

const handleApprove = async (wo) => {
    if (wo.pembuat_id === currentUserId.value) {
        alert('Akses Ditolak: Anda adalah pemberi tugas. Hanya penerima tugas (PIC) yang dapat menyelesaikan tugas ini.');
        return;
    }
    if (confirm('Konfirmasi: Tandai tugas ini sebagai selesai?')) {
        await approveTask(wo.id)
    }
}

const openChatModal = async (wo) => {
    activeWO.value = { ...wo, pesan_chat: [] }
    isChatOpen.value = true
    activeWO.value.pesan_chat = await fetchChat(wo.id)
    scrollToBottom()
}

const kirimPesan = async () => {
    if (!activeWO.value || !chatInput.value.trim()) return
    const pesanBaru = await sendReply(activeWO.value.id, chatInput.value)
    if (pesanBaru) {
        activeWO.value.pesan_chat.push(pesanBaru)
        chatInput.value = ''
        scrollToBottom()
        fetchMading()
    }
}

const scrollToBottom = () => {
    nextTick(() => {
        if (chatBox.value) {
            chatBox.value.scrollTop = chatBox.value.scrollHeight
        }
    })
}
</script>

<style scoped>
.wo-board {
    box-sizing: border-box;
    padding: 2rem;
    max-width: 1440px;
    margin: 0 auto;
    font-family: 'Inter', -apple-system, sans-serif;
    color: #0f172a;
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

.wo-loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
    padding: 5rem 0;
    color: #64748b;
    font-size: 0.875rem;
    font-weight: 500;
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

.wo-empty {
    padding: 5rem 2rem;
    text-align: center;
    background: linear-gradient(to bottom, #ffffff, #f8fafc);
    border: 1px dashed #cbd5e1;
    border-radius: 16px;
}

.empty-glow {
    width: 5rem;
    height: 5rem;
    margin: 0 auto 1.5rem auto;
    background: #f0fdfa;
    color: #0d9488;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2rem;
    box-shadow: 0 0 30px rgba(13, 148, 136, 0.15);
    border: 1px solid #ccfbf1;
}

.wo-empty h3 {
    font-size: 1.25rem;
    font-weight: 700;
    margin: 0 0 0.5rem;
    color: #1e293b;
}

.wo-empty p {
    color: #64748b;
    font-size: 0.9375rem;
    margin: 0;
}

.wo-grid {
    display: grid;
    gap: 1.5rem;
}

.wo-grid[data-count="1"] {
    grid-template-columns: 1fr;
    max-width: 450px;
}

.wo-grid[data-count="2"] {
    grid-template-columns: repeat(2, 1fr);
    max-width: 900px;
}

.wo-grid[data-count="3"] {
    grid-template-columns: repeat(3, 1fr);
}

.wo-grid[data-count="4"],
.wo-grid[data-count="more"] {
    grid-template-columns: repeat(4, 1fr);
}

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
    box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.01);
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

.chat-wrapper {
    display: flex;
    flex-direction: column;
    height: 420px;
}

.chat-feed {
    flex: 1;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 1rem;
    padding-right: 0.5rem;
}

.chat-blank {
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    color: #94a3b8;
    font-size: 0.875rem;
}

.chat-blank i {
    font-size: 2rem;
    margin-bottom: 0.5rem;
    opacity: 0.5;
}

.message-block {
    display: flex;
    flex-direction: column;
}

.sender-id {
    font-size: 0.65rem;
    font-weight: 700;
    color: #64748b;
    margin-bottom: 0.2rem;
    margin-left: 0.5rem;
    text-transform: uppercase;
}

.message-core {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    padding: 0.75rem 1rem;
    border-radius: 12px;
    border-top-left-radius: 2px;
    font-size: 0.875rem;
    color: #1e293b;
    width: fit-content;
    max-width: 90%;
    line-height: 1.4;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
}

.chat-control {
    margin-top: 1.25rem;
    display: flex;
    gap: 0.5rem;
}

.btn-send-tech {
    background: #0f172a;
    color: #fff;
    width: 2.75rem;
    height: 2.75rem;
    border: none;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: 0.2s;
}

.btn-send-tech:hover:not(:disabled) {
    background: #14b8a6;
}

.btn-send-tech:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.custom-scroll::-webkit-scrollbar {
    width: 5px;
}

.custom-scroll::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 10px;
}

@media (max-width: 1024px) {
    .wo-grid[data-count="3"],
    .wo-grid[data-count="4"],
    .wo-grid[data-count="more"] {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (max-width: 768px) {
    .wo-board {
        padding: 1rem;
    }
    .wo-grid[data-count] {
        grid-template-columns: 1fr;
        max-width: 100%;
    }
    .form-row {
        grid-template-columns: 1fr;
    }
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
