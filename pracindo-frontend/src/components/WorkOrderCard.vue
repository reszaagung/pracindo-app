<!--
  components/WorkOrderCard.vue
  ============================
  Dipakai di dashboard dan (nanti) di halaman work order penuh.

  Tombol approve hanya muncul untuk staf yang DI-TAG — backend juga
  menegakkan ini, jadi menyembunyikan tombol murni soal kejelasan.
  Satu approval menutup WO untuk semua yang ditag.
-->
<template>
    <article class="wo" :class="{ 'wo--telat': wo.terlambat }">
        <div class="wo__atas">
            <span class="wo__nomor">{{ wo.nomor }}</span>
            <span v-if="wo.terlambat" class="wo__telat">Lewat tenggat</span>
            <span v-else-if="tenggat" class="wo__tempo">{{ tenggat }}</span>
        </div>

        <h3 class="wo__judul">{{ wo.judul }}</h3>
        <p v-if="wo.deskripsi" class="wo__desk">{{ wo.deskripsi }}</p>

        <div class="wo__bawah">
            <div class="wo__orang">
                <span v-for="p in wo.penugasan" :key="p.id" class="wo__tag"
                    :class="{ 'wo__tag--saya': p.staff === staffId }">{{ p.staff_nama }}</span>
            </div>

            <button v-if="bisaApprove" class="wo__ok" :disabled="sibuk" @click="$emit('approve', wo)">{{ sibuk ?
                'Menyimpan' : 'Sudah dikerjakan' }}</button>
        </div>
    </article>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
    wo: { type: Object, required: true },
    staffId: { type: Number, default: null },
    sibuk: { type: Boolean, default: false },
})
defineEmits(['approve'])

const bisaApprove = computed(() =>
    !props.wo.selesai && props.wo.penugasan?.some(p => p.staff === props.staffId),
)

const tenggat = computed(() => {
    if (!props.wo.deadline) return ''
    const d = new Date(props.wo.deadline)
    const jam = Math.round((d - Date.now()) / 3_600_000)
    if (jam < 0) return ''
    if (jam < 24) return `${jam} jam lagi`
    return d.toLocaleDateString('id-ID', { day: 'numeric', month: 'short' })
})
</script>

<style scoped>
.wo {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-left: 4px solid #CBD5E1;
    border-radius: 8px;
    padding: 1.25rem;
    transition: all .2s ease;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
}

.wo:hover {
    border-color: #94A3B8;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}

.wo--telat {
    border-left-color: #EF4444;
}

.wo__atas {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: 1rem;
    margin-bottom: .6rem;
}

.wo__nomor {
    font-size: .6875rem;
    font-weight: 700;
    letter-spacing: .05em;
    color: #64748B;
}

.wo__telat {
    font-size: .625rem;
    font-weight: 700;
    letter-spacing: .06em;
    text-transform: uppercase;
    color: #B91C1C;
    background: #FEF2F2;
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
}

.wo__tempo {
    font-size: .75rem;
    font-weight: 500;
    color: #64748B;
}

.wo__judul {
    margin: 0 0 .4rem;
    font-size: 1rem;
    font-weight: 600;
    color: #0F172A;
    line-height: 1.4;
}

.wo__desk {
    margin: 0;
    font-size: .875rem;
    color: #475569;
    line-height: 1.5;
}

.wo__bawah {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    gap: .75rem;
    flex-wrap: wrap;
    margin-top: 1.25rem;
    padding-top: 1rem;
    border-top: 1px dashed #E2E8F0;
}

.wo__orang {
    display: flex;
    gap: .4rem;
    flex-wrap: wrap;
}

.wo__tag {
    font-size: .75rem;
    color: #64748B;
    background: #F1F5F9;
    padding: .25rem .6rem;
    border-radius: 999px;
    font-weight: 500;
}

.wo__tag--saya {
    color: #2563EB;
    background: #EFF6FF;
}

.wo__ok {
    font-family: inherit;
    font-size: .8125rem;
    font-weight: 600;
    color: #fff;
    background: #10B981;
    border: none;
    padding: .5rem 1rem;
    border-radius: 6px;
    cursor: pointer;
    transition: all .15s ease;
    box-shadow: 0 1px 2px rgba(16, 185, 129, 0.2);
}

.wo__ok:hover:not(:disabled) {
    background: #059669;
}

.wo__ok:disabled {
    background: #94A3B8;
    cursor: not-allowed;
    box-shadow: none;
}
</style>