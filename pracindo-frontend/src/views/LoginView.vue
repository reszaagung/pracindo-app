<!--
  src/views/LoginView.vue
  ========================
  UI/UX dipertahankan sepenuhnya menggunakan CSS MURNI (Custom CSS).
  Logika telah disinkronkan dengan:
  1. Parameter `next` dari router guards.
  2. Penangkap notifikasi token kedaluwarsa.
  3. Tautan Registrasi Staff yang mengarah ke /register.
-->
<template>
    <div class="login-wrapper">

        <!-- ── kiri: panel ilustrasi (desktop) ─────────────────── -->
        <div class="panel-left">
            <div class="brand-top">
                <img :src="logoPracindo" alt="Logo Pracindo" class="logo-img" />
                <span class="brand-text">Pracindo Supply Chain Management</span>
            </div>

            <div class="hero-content">
                <h1 class="hero-title">
                    Aplikasi <br>
                    Utama untuk <br>
                    <span class="text-teal">Kontrol Manufaktur.</span>
                </h1>

                <p class="hero-subtitle">
                    Aplikasi untuk mengelola rantai pasok, proses produksi, pembukuan,
                    inventaris gudang, hingga distribusi lapangan.
                </p>

                <div class="illustration-wrap">
                    <img :src="ilustrationImg" alt="Ilustrasi Central Hub" class="hero-img" />
                </div>
            </div>
        </div>

        <!-- ── kanan: form login ───────────────────────────────── -->
        <div class="panel-right">
            <div class="login-box animate-fade-in">

                <!-- Tampil hanya di Mobile -->
                <div class="mobile-brand">
                    <img :src="logoPracindo" alt="Logo Pracindo" class="logo-img-mobile" />
                    <span class="brand-text-mobile">Pracindo Jaya Mandiri</span>
                </div>

                <h2 class="form-title">Login Staff</h2>

                <form class="login-form" @submit.prevent="handleLogin">
                    <div class="input-group">
                        <input ref="isianPertama" v-model="form.identifier" type="text"
                            placeholder="Username atau email" autocomplete="username" required :disabled="sedangProses"
                            class="form-input" />
                    </div>

                    <div class="input-group relative">
                        <input v-model="form.password" :type="showPassword ? 'text' : 'password'"
                            placeholder="Kata Sandi" autocomplete="current-password" required :disabled="sedangProses"
                            class="form-input pr-icon" />
                        <button type="button" class="btn-toggle-pass"
                            :aria-label="showPassword ? 'Sembunyikan sandi' : 'Tampilkan sandi'"
                            @click="showPassword = !showPassword">
                            <i :class="showPassword ? 'pi pi-eye-slash' : 'pi pi-eye'"></i>
                        </button>
                    </div>

                    <!-- Pesan Error / Notifikasi Sesi -->
                    <p v-if="pesan" role="alert" class="error-msg">
                        {{ pesan }}
                    </p>

                    <button type="submit" class="btn-submit" :disabled="sedangProses">
                        <i v-if="sedangProses" class="pi pi-spin pi-spinner" style="margin-right: 8px;"></i>
                        {{ sedangProses ? 'Memeriksa...' : 'Login' }}
                    </button>
                </form>

                <div class="divider"></div>

                <!-- Tautan ke Halaman Pendaftaran -->
                <p class="register-link-wrap">
                    Belum punya akun? <br>
                    <router-link to="/register" class="register-link">
                        Registrasi Staff
                    </router-link>
                </p>

                <p class="session-warning">
                    Satu sesi aktif per akun — masuk di perangkat lain akan menutup sesi ini.
                </p>
            </div>

            <div class="footer-note">
                <i class="pi pi-shield"></i> Pracindo Central Hub
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import { rutePertamaSiap } from '@/config/modules'

import logoPracindo from '@/assets/logo_pt.svg'
import ilustrationImg from '@/assets/ilustration.jpg'

const route = useRoute()
const router = useRouter()
const { login, sedangProses, bisaAkses, modul } = useAuth()

const form = reactive({ identifier: '', password: '' })
const showPassword = ref(false)
const pesan = ref('')
const isianPertama = ref(null)

onMounted(() => {
    isianPertama.value?.focus?.()
    if (route.query.sesi === 'berakhir') {
        pesan.value = 'Sesi Anda telah berakhir. Silakan login kembali.'
        router.replace({ query: {} })
    }
})

const handleLogin = async () => {
    pesan.value = ''
    const hasil = await login(form.identifier.trim(), form.password)

    if (!hasil.success) {
        pesan.value = hasil.message
        form.password = ''
        return
    }
    const tujuan = route.query.next
    if (bolehKe(tujuan)) {
        router.push(tujuan)
        return
    }

    router.push(rutePertamaSiap(modul.value) ?? { name: 'dashboard' })
}

const bolehKe = (tujuan) => {
    if (typeof tujuan !== 'string' || !tujuan.startsWith('/')) return false
    if (tujuan === '/' || tujuan.startsWith('//')) return false

    const cocok = router.resolve(tujuan)
    if (cocok.name === 'NotFound') return false

    const kodeModul = cocok.meta?.modul
    return !kodeModul || bisaAkses(kodeModul)
}
</script>

<style scoped>
/* =========================================
   STYLE MURNI HALAMAN LOGIN (TANPA TAILWIND)
========================================= */

* {
    box-sizing: border-box;
}

.login-wrapper {
    display: flex;
    min-height: 100vh;
    width: 100%;
    font-family: inherit;
    color: #1e293b;
    background: #fff;
    overflow: hidden;
}

/* --- KIRI: PANEL ILUSTRASI --- */
.panel-left {
    display: none;
    /* Sembunyikan di HP */
    width: 55%;
    flex-direction: column;
    justify-content: center;
    position: relative;
    padding: 4rem 6rem;
    border-right: 1px solid #e2e8f0;
}

@media (min-width: 1024px) {
    .panel-left {
        display: flex;
    }
}

.brand-top {
    position: absolute;
    top: 3rem;
    left: 6rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.logo-img {
    width: 4rem;
    height: 4rem;
    object-fit: contain;
    border-radius: 0.75rem;
    border: 1px solid #e2e8f0;
    padding: 0.25rem;
}

.brand-text {
    font-weight: 700;
    font-size: 1.25rem;
    color: #0f766e;
    letter-spacing: -0.025em;
}

.hero-content {
    width: 100%;
    z-index: 10;
    margin-top: 2rem;
}

.hero-title {
    font-size: 3.5rem;
    font-weight: 700;
    color: #0f172a;
    line-height: 1.1;
    letter-spacing: -0.025em;
    margin-bottom: 1rem;
}

.text-teal {
    color: #0d9488;
}

.hero-subtitle {
    font-size: 1rem;
    color: #475569;
    margin-bottom: 2rem;
    font-weight: 500;
    line-height: 1.625;
    max-width: 36rem;
}

.illustration-wrap {
    position: relative;
    width: 100%;
    max-width: 700px;
    margin-top: 0.5rem;
}

.hero-img {
    width: 100%;
    aspect-ratio: 21/10;
    object-fit: contain;
    object-position: left;
    border-radius: 0.75rem;
    filter: drop-shadow(0 4px 6px rgba(0, 0, 0, 0.1));
}

/* --- KANAN: PANEL FORM LOGIN --- */
.panel-right {
    width: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 2rem;
    position: relative;
    background: #f8fafc;
}

@media (min-width: 1024px) {
    .panel-right {
        width: 45%;
        background: #fff;
    }
}

.login-box {
    width: 100%;
    max-width: 400px;
    background: #fff;
    padding: 2rem;
    border-radius: 1rem;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.08);
    border: 1px solid #e2e8f0;
}

/* Brand Khusus Mobile */
.mobile-brand {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 2rem;
}

@media (min-width: 1024px) {
    .mobile-brand {
        display: none;
    }
}

.logo-img-mobile {
    width: 5rem;
    height: 5rem;
    object-fit: contain;
    border-radius: 0.75rem;
    border: 1px solid #e2e8f0;
    padding: 0.375rem;
}

.brand-text-mobile {
    font-weight: 700;
    font-size: 1.5rem;
    color: #0d9488;
    letter-spacing: -0.025em;
}

.form-title {
    font-size: 1.25rem;
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 1.5rem;
    text-align: center;
}

/* Form Styling */
.login-form {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.input-group {
    position: relative;
    width: 100%;
}

.form-input {
    width: 100%;
    border-radius: 0.75rem;
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    padding: 0.875rem 1rem;
    font-size: 0.9375rem;
    color: #334155;
    transition: all 0.2s;
    outline: none;
    font-family: inherit;
}

.form-input:focus {
    border-color: #14b8a6;
    box-shadow: 0 0 0 2px rgba(20, 184, 166, 0.2);
    background: #fff;
}

.form-input.pr-icon {
    padding-right: 3rem;
}

.btn-toggle-pass {
    position: absolute;
    right: 1rem;
    top: 50%;
    transform: translateY(-50%);
    background: none;
    border: none;
    color: #94a3b8;
    cursor: pointer;
    font-size: 1.125rem;
}

.btn-toggle-pass:hover {
    color: #475569;
}

/* Error Message */
.error-msg {
    background: #fef2f2;
    border: 1px solid #fee2e2;
    color: #dc2626;
    font-size: 0.875rem;
    line-height: 1.5;
    border-radius: 0.75rem;
    padding: 0.75rem 1rem;
    margin: 0;
    white-space: pre-line;
}

/* Tombol Submit */
.btn-submit {
    width: 100%;
    background: #0d9488;
    color: #fff;
    border: none;
    border-radius: 0.75rem;
    padding: 0.875rem;
    font-size: 1.0625rem;
    font-weight: 700;
    cursor: pointer;
    transition: background 0.2s;
    margin-top: 0.5rem;
    font-family: inherit;
    display: flex;
    justify-content: center;
    align-items: center;
}

.btn-submit:hover:not(:disabled) {
    background: #0f766e;
}

.btn-submit:disabled {
    opacity: 0.7;
    cursor: not-allowed;
}

.divider {
    border-bottom: 1px solid #e2e8f0;
    width: 100%;
    margin: 1.5rem 0 1.25rem 0;
}

/* Register Link & Text Bawah */
.register-link-wrap {
    text-align: center;
    font-size: 0.875rem;
    color: #64748b;
    font-weight: 500;
    margin: 0;
    line-height: 1.5;
}

.register-link {
    color: #0d9488;
    font-weight: 700;
    text-decoration: none;
    transition: color 0.2s;
}

.register-link:hover {
    color: #0f766e;
}

.session-warning {
    margin-top: 1.25rem;
    padding-top: 1rem;
    border-top: 1px solid #e2e8f0;
    font-size: 0.75rem;
    color: #94a3b8;
    text-align: center;
    line-height: 1.5;
}

.footer-note {
    position: absolute;
    bottom: 2rem;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.375rem;
    color: #94a3b8;
    font-size: 0.875rem;
    font-weight: 500;
}

/* --- ANIMASI --- */
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

@media (prefers-reduced-motion: reduce) {
    .animate-fade-in {
        animation: none;
    }
}
</style>