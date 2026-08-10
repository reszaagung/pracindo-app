<!--
  views/AksesDitolak.vue
  =======================
  403 yang menyebut modul apa yang dicoba dan peran apa yang dipakai.

  Sebelumnya penolakan memakai alert() lalu `return false` — alert memblokir
  thread, dan `return false` berarti pengguna mengklik sesuatu dan TIDAK
  TERJADI APA-APA. Keduanya membuat penolakan terasa seperti aplikasi rusak,
  bukan seperti keputusan yang disengaja.

  Halaman ini sengaja TIDAK punya meta.modul — kalau punya, guard akan
  menolaknya juga dan redirect-nya berputar tanpa henti.
-->
<template>
    <div class="tolak">
        <span class="tolak__tanda">403</span>
        <h1 class="tolak__judul">Akses ditolak</h1>

        <p class="tolak__teks">
            <template v-if="kodeModul">
                Peran <strong>{{ peran }}</strong> tidak punya akses ke modul
                <code class="tolak__modul">{{ namaModul }}</code>.
            </template>
            <template v-else>
                Peran <strong>{{ peran }}</strong> tidak punya akses ke halaman itu.
            </template>
            Kalau kamu memang seharusnya bisa membukanya, minta Supervisor
            menyesuaikan peran akunmu — daftar modul datang dari server,
            bukan dari aplikasi ini.
        </p>

        <router-link :to="{ name: 'dashboard' }" class="tolak__balik">
            Kembali ke dashboard
        </router-link>
    </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import { cariModul } from '@/config/modules'

const route = useRoute()
const { kartu } = useAuth()

const kodeModul = computed(() => {
    const q = route.query.modul
    return typeof q === 'string' && q ? q : ''
})

// Nama ramah dari katalog; kalau modulnya tidak dikenal, tampilkan kodenya
// apa adanya supaya tetap bisa dilaporkan.
const namaModul = computed(() =>
    cariModul(kodeModul.value)?.nama ?? kodeModul.value)

const peran = computed(() => kartu.value?.role_display ?? 'kamu')
</script>

<style scoped>
.tolak {
    max-width: 34rem;
    margin: 0 auto;
    padding: 5rem clamp(1rem, 4vw, 2.5rem);
    text-align: center;
}

.tolak__tanda {
    font-size: .75rem;
    font-weight: 700;
    letter-spacing: .1em;
    color: var(--redup-2);
}

.tolak__judul {
    margin: .6rem 0 .5rem;
    font-size: 1.5rem;
    font-weight: 700;
    letter-spacing: -.02em;
}

.tolak__teks {
    margin: 0 0 1.75rem;
    font-size: .9375rem;
    color: var(--redup);
    line-height: 1.6;
}

.tolak__modul {
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    font-size: .875rem;
    background: var(--latar);
    border: 1px solid var(--garis);
    border-radius: var(--lengkung-kecil);
    padding: .1rem .35rem;
    word-break: break-all;
}

.tolak__balik {
    font-size: .8125rem;
    color: var(--redup);
    text-decoration: none;
    border: 1px solid var(--garis);
    border-radius: var(--lengkung-kecil);
    padding: .5rem .9rem;
}

.tolak__balik:hover {
    border-color: var(--garis-tegas);
    color: var(--teks);
}
</style>
