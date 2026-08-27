<!--
  layouts/ModulLayout.vue
  =======================
  Wrapper bersidebar untuk SEMUA halaman di dalam modul. Dashboard TIDAK
  memakai ini — sidebar hanya muncul setelah masuk modul.

  Modul ditentukan dari route.meta.modul, lalu menu sidebar dibaca dari
  config/modules.js. Menambah menu = sunting config, bukan komponen ini.

  BREAKPOINT: satu-satunya sumber kebenaran adalah TITIK_PUTUS di
  constant/layout.js, dibaca lewat isMobile dari useLayout(). Tidak ada
  @media di sini -- versi lama punya @media (max-width: 900px) yang
  menyimpang dari TITIK_PUTUS (1024px), menciptakan rentang 900-1024px
  di mana JS dan CSS saling bertentangan soal "apakah ini mobile".
-->
<template>
    <div class="rangka" :class="{ 'rangka--mobile': isMobile }">
        <nav class="side" :class="{ 'side--buka': sidebarAktif, 'side--mobile': isMobile }">
            <router-link to="/" class="side__balik">
                <BaseIcon nama="balik" :ukuran="15" />
                Semua modul
            </router-link>

            <h2 class="side__judul">{{ modul?.nama }}</h2>

            <ul class="side__menu">
                <li v-for="m in modul?.menu ?? []" :key="m.rute">
                    <router-link :to="m.rute" class="side__tautan" active-class="on" :exact="m.rute === modul.rute">
                        {{ m.label }}
                    </router-link>
                </li>
            </ul>

            <div class="side__kaki">
                {{ kartu.nama }} · {{ kartu.role_display }}
            </div>
        </nav>

        <div v-if="isMobile && sidebarAktif" class="overlay" @click="tutupDiMobile" />

        <main class="isi">
            <button v-if="isMobile" class="buka-side" @click="toggleSidebar" aria-label="Buka menu">
                <span></span><span></span><span></span>
            </button>

            <section class="mt-16 pt-8 border-t border-slate-200">
                <WorkOrderPanel />
            </section>
        </main>
    </div>
</template>

<script setup>
import { computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { cariModul } from '@/config/modules'
import { useAuth } from '@/composables/useAuth'
import { useLayout } from '@/composables/useLayout'
import BaseIcon from '@/components/ui/BaseIcon.vue'
import WorkOrderPanel from '@/features/work-order/views/WorkOrderBoard.vue'

const route = useRoute()
const { kartu: kartuAuth } = useAuth()
const { sidebarAktif, isMobile, toggleSidebar, tutupDiMobile } = useLayout()

const kartu = computed(() => kartuAuth.value ?? { nama: '—', role_display: '—' })
const modul = computed(() => cariModul(route.meta?.modul))

watch(() => route.fullPath, tutupDiMobile)
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
    transition: opacity 0.25s ease-out, transform 0.25s ease-out;
}

.fade-enter-from {
    opacity: 0;
    transform: translateY(10px);
}

.fade-leave-to {
    opacity: 0;
    transform: translateY(-10px);
}

.rangka {
    display: grid;
    grid-template-columns: 224px 1fr;
    min-height: 100vh;
}

.rangka--mobile {
    grid-template-columns: 1fr;
}

.side {
    background: var(--panel);
    border-right: 1px solid var(--garis);
    padding: 1.25rem 0;
    position: sticky;
    top: 0;
    height: 100vh;
    display: flex;
    flex-direction: column;
}

.side--mobile {
    position: fixed;
    inset: 0 auto 0 0;
    width: 224px;
    z-index: 20;
    transform: translateX(-100%);
    transition: transform .22s ease;
    box-shadow: var(--bayang-angkat);
}

.side--mobile.side--buka {
    transform: none;
}

.side__balik {
    display: flex;
    align-items: center;
    gap: .5rem;
    margin: 0 1.1rem 1.15rem;
    padding-bottom: 1.15rem;
    border-bottom: 1px solid var(--garis);
    font-size: .8125rem;
    color: var(--redup);
    text-decoration: none;
}

.side__balik:hover {
    color: var(--teks);
}

.side__judul {
    margin: 0 1.1rem .85rem;
    font-size: .6875rem;
    font-weight: 700;
    letter-spacing: .1em;
    text-transform: uppercase;
    color: var(--redup-2);
}

.side__menu {
    list-style: none;
    margin: 0;
    padding: 0 .6rem;
}

.side__menu li {
    margin-bottom: .15rem;
}

.side__tautan {
    display: block;
    font-size: .8125rem;
    color: var(--teks-2);
    padding: .6rem .7rem;
    border-radius: var(--lengkung-kecil);
    text-decoration: none;
}

.side__tautan:hover {
    background: var(--latar);
    color: var(--teks);
}

.side__tautan.on {
    background: var(--teks);
    color: var(--panel);
    font-weight: 600;
}

.side__kaki {
    margin-top: auto;
    padding: 1rem 1.1rem 0;
    border-top: 1px solid var(--garis);
    font-size: .75rem;
    color: var(--redup-2);
}

.overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.4);
    z-index: 15;
}

.isi {
    padding: 1.75rem clamp(1rem, 3vw, 2.25rem) 3rem;
    min-width: 0;
}

.buka-side {
    display: flex;
    flex-direction: column;
    gap: 4px;
    background: var(--panel);
    border: 1px solid var(--garis);
    border-radius: var(--lengkung-kecil);
    padding: .6rem;
    margin-bottom: 1rem;
    cursor: pointer;
}

.buka-side span {
    width: 16px;
    height: 2px;
    background: var(--teks);
    display: block;
}
</style>
