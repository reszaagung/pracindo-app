<!--
  components/ModuleCard.vue
  =========================
  Kartu navigasi di dashboard. Modul yang belum siap tampil REDUP dengan
  label "segera", bukan disembunyikan — menyembunyikan membuat orang
  bertanya kenapa menu hilang; menampilkan redup memberi tahu bahwa itu
  memang belum ada, bukan rusak.
-->
<template>
    <component :is="modul.siap ? 'router-link' : 'div'" :to="modul.siap ? modul.rute : undefined" class="nav"
        :class="{ 'nav--tunggu': !modul.siap }" :aria-disabled="!modul.siap">
        <span v-if="hitung" class="nav__hitung">{{ hitung }}</span>
        <span v-else-if="!modul.siap" class="nav__segera">segera</span>

        <span class="nav__lambang">
            <BaseIcon :nama="modul.ikon" :ukuran="21" />
        </span>

        <span class="nav__teks">
            <span class="nav__nama">{{ modul.nama }}</span>
            <span class="nav__ringkas">{{ modul.siap ? modul.ringkas : (modul.catatan || 'Belum tersedia') }}</span>
        </span>

        <span v-if="modul.siap" class="nav__panah" aria-hidden="true">
            <BaseIcon nama="panah" :ukuran="17" />
        </span>
    </component>
</template>

<script setup>
import BaseIcon from '@/components/ui/BaseIcon.vue'

defineProps({
    modul: { type: Object, required: true },
    hitung: { type: [Number, String], default: 0 },
})
</script>

<style scoped>
.nav {
    position: relative;
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1.35rem;
    background: var(--panel);
    border: 1px solid var(--garis);
    border-radius: var(--lengkung);
    color: inherit;
    text-decoration: none;
    transition: border-color .16s ease, transform .16s ease, box-shadow .16s ease;
}

.nav:hover:not(.nav--tunggu) {
    border-color: var(--garis-tegas);
    transform: translateY(-2px);
    box-shadow: var(--bayang-angkat);
}

.nav--tunggu {
    opacity: .5;
    cursor: default;
}

.nav__lambang {
    width: 44px;
    height: 44px;
    border-radius: 11px;
    display: grid;
    place-items: center;
    background: var(--biru-latar);
    color: var(--biru);
    flex-shrink: 0;
}

.nav__teks {
    display: flex;
    flex-direction: column;
    gap: .25rem;
    min-width: 0;
    flex: 1;
}

.nav__nama {
    font-size: 1rem;
    font-weight: 600;
}

.nav__ringkas {
    font-size: .8125rem;
    color: var(--redup);
    line-height: 1.45;
}

.nav__panah {
    color: var(--redup-2);
    display: flex;
    opacity: 0;
    transform: translateX(-4px);
    transition: all .18s ease;
}

.nav:hover .nav__panah {
    opacity: 1;
    transform: none;
    color: var(--teks);
}

.nav__hitung {
    position: absolute;
    top: 1.1rem;
    right: 1.1rem;
    font-size: .6875rem;
    font-weight: 700;
    color: var(--merah);
    background: var(--merah-latar);
    padding: .15rem .45rem;
    border-radius: 6px;
}

.nav__segera {
    position: absolute;
    top: 1.1rem;
    right: 1.1rem;
    font-size: .625rem;
    font-weight: 600;
    letter-spacing: .06em;
    text-transform: uppercase;
    color: var(--redup-2);
    border: 1px solid var(--garis);
    padding: .12rem .4rem;
    border-radius: 5px;
}
</style>