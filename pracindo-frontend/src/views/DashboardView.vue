<!--
  views/DashboardView.vue
  =======================
  Layar pertama setelah login. SENGAJA TANPA SIDEBAR — dashboard adalah
  halaman pemilihan modul; sidebar baru muncul setelah masuk ke modul
  (lihat layouts/ModulLayout.vue).
-->
<template>
    <div class="dash">
        <header class="dash__kepala">
            <div>
                <div class="merek">
                    <span class="merek__kotak">PC</span>
                    <span class="merek__teks">Pracindo · Sistem Internal</span>
                </div>
                <!-- Menggunakan sapaan computed yang aman -->
                <h1 class="sapa">{{ sapaan }}, {{ namaDepan }}</h1>
                <p class="sub">Pilih modul untuk mulai bekerja.</p>
            </div>

            <div class="orang">
                <p class="orang__nama">{{ kartu?.nama ?? 'Pengguna' }}</p>
                <p class="orang__peran">
                    {{ kartu?.role_display ?? 'Staf' }} · {{ kartu?.entitas_default_kode ?? 'Semua entitas' }}
                </p>
                <button class="orang__keluar" @click="keluar">Keluar</button>
            </div>
        </header>

        <!-- BAGIAN ATAS: KARTU MODUL -->
        <section class="blok">
            <h2 class="stensil">Modul</h2>
            <div class="kartu">
                <ModuleCard v-for="m in modulSaya" :key="m.id" :modul="m" />
            </div>

            <p v-if="modulSaya.length < MODUL_KATALOG.length - 1" class="blok__kaki">
                Modul yang tidak muncul di sini di luar tanggung jawab
                {{ (kartu?.role_display ?? 'staf').toLowerCase() }}.
            </p>
        </section>

        <!-- BAGIAN BAWAH: PAPAN TUGAS GLOBAL -->
        <section class="blok w-full mt-10">
            <WorkOrderPanel />
        </section>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

import { useAuth } from '@/composables/useAuth'
import { MODUL as MODUL_KATALOG, modulDariBackend } from '@/config/modules'
import ModuleCard from '@/components/ModuleCard.vue'

import WorkOrderPanel from '@/features/work-order/views/WorkOrderBoard.vue'

const router = useRouter()
const { kartu, modul, logout } = useAuth()
const modulSaya = computed(() => {
    const peran = kartu.value?.role || ''
    const tampil = (m) =>
        !m.sembunyiDiDashboard && !(m.sembunyiDiDashboardUntuk ?? []).includes(peran)

    return modulDariBackend(modul.value)
        .flatMap(m => [m, ...MODUL_KATALOG.filter(k => k.indukModul === m.id)])
        .filter(tampil)
})

const namaDepan = computed(() => {
    const nama = kartu.value?.nama || ''
    return nama.split(' ')[0] || 'Pengguna'
})

const sekarang = ref(new Date())
let timer = null

onMounted(() => {
    timer = setInterval(() => (sekarang.value = new Date()), 60_000)
})

onUnmounted(() => clearInterval(timer))

const sapaan = computed(() => {
    const h = sekarang.value.getHours()
    if (h < 11) return 'Selamat pagi'
    if (h < 15) return 'Selamat siang'
    if (h < 18) return 'Selamat sore'
    return 'Selamat malam'
})

const keluar = async () => {
    await logout()
    router.push('/login')
}
</script>
<style scoped>
.dash {
    max-width: 1180px;
    margin: 0 auto;
    padding: 2.5rem clamp(1rem, 4vw, 2.5rem) 4rem;
}

.dash__kepala {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 2rem;
    flex-wrap: wrap;
    padding-bottom: 1.75rem;
    border-bottom: 1px solid var(--garis);
}

.merek {
    display: flex;
    align-items: center;
    gap: .7rem;
    margin-bottom: 1.1rem;
}

.merek__kotak {
    width: 34px;
    height: 34px;
    background: var(--teks);
    color: var(--panel);
    display: grid;
    place-items: center;
    font-weight: 700;
    font-size: .75rem;
    border-radius: var(--lengkung-kecil);
}

.merek__teks {
    font-size: .75rem;
    font-weight: 600;
    letter-spacing: .1em;
    text-transform: uppercase;
    color: var(--redup-2);
}

.sapa {
    margin: 0;
    font-size: clamp(1.6rem, 4vw, 2rem);
    font-weight: 700;
    letter-spacing: -.025em;
}

.sub {
    margin: .35rem 0 0;
    font-size: .9375rem;
    color: var(--redup);
}

.orang {
    text-align: right;
}

.orang__nama {
    margin: 0;
    font-size: .875rem;
    font-weight: 600;
}

.orang__peran {
    margin: .15rem 0 0;
    font-size: .75rem;
    color: var(--redup-2);
}

.orang__keluar {
    margin-top: .65rem;
    font-family: inherit;
    font-size: .75rem;
    color: var(--redup);
    background: none;
    border: 1px solid var(--garis);
    padding: .38rem .75rem;
    border-radius: var(--lengkung-kecil);
    cursor: pointer;
}

.orang__keluar:hover {
    border-color: var(--garis-tegas);
    color: var(--teks);
}

.blok {
    margin-top: 2rem;
}

.blok__kepala {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
}

.blok .stensil {
    margin-bottom: 1rem;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--redup-2);
}

.blok__kepala .stensil {
    margin-bottom: 0;
}

.blok__kepala+* {
    margin-top: 1rem;
}

.tautan {
    font-size: .75rem;
    color: var(--redup);
    text-decoration: none;
    border-bottom: 1px solid transparent;
}

.tautan:hover {
    color: var(--teks);
    border-bottom-color: var(--garis-tegas);
}

.kartu {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(19rem, 1fr));
    gap: 1rem;
}

.blok__kaki {
    margin: 1rem 0 0;
    font-size: .8125rem;
    color: var(--redup-2);
}
</style>