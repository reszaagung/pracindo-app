<!-- src/views/RegisterView.vue -->
<template>
    <div class="register-wrapper">
        <div class="register-box animate-fade-in">

            <div class="header">
                <div class="icon-wrap">
                    <i class="pi pi-user-plus"></i>
                </div>
                <h2 class="title">Registrasi Staff</h2>
                <p class="subtitle">Lengkapi data diri Anda untuk meminta akses Pracindo ERP.</p>
            </div>
            <div v-if="sukses" class="alert alert-success animate-fade-in">
                <i class="pi pi-check-circle icon-large"></i>
                <h3>Pendaftaran Berhasil</h3>
                <p>{{ sukses }}</p>
                <router-link to="/login" class="link-back-success">
                    <i class="pi pi-arrow-left"></i> Lanjut ke halaman Login
                </router-link>
            </div>
            <form v-else class="register-form" @submit.prevent="handleDaftar">
                <div v-if="pesan" class="alert alert-error animate-fade-in">
                    <i class="pi pi-exclamation-triangle"></i>
                    <span>{{ pesan }}</span>
                </div>

                <div class="input-group full-width">
                    <label>Nama Lengkap</label>
                    <input v-model="daftarForm.nama_lengkap" type="text" required placeholder="Masukkan nama lengkap"
                        class="form-input" :disabled="sedangProses" />
                </div>

                <div class="form-grid">
                    <div class="input-group">
                        <label>Username</label>
                        <input v-model="daftarForm.username" type="text" required placeholder="Contoh: budi.gudang"
                            class="form-input" :disabled="sedangProses" />
                    </div>
                    <div class="input-group">
                        <label>Telepon / WhatsApp</label>
                        <input v-model="daftarForm.telepon" type="text" placeholder="08xxxxxxx" class="form-input"
                            :disabled="sedangProses" />
                    </div>
                </div>

                <div class="input-group full-width">
                    <label>Email</label>
                    <input v-model="daftarForm.email" type="email" required placeholder="email@pracindo.com"
                        class="form-input" :disabled="sedangProses" />
                </div>

                <div class="form-grid">
                    <div class="input-group">
                        <label>Kata Sandi</label>
                        <div class="input-with-icon">
                            <input v-model="daftarForm.password" :type="showPassword ? 'text' : 'password'" required
                                minlength="10" placeholder="Minimal 10 karakter" class="form-input"
                                :disabled="sedangProses" />
                            <button type="button" class="btn-toggle" @click="showPassword = !showPassword"
                                tabindex="-1">
                                <i :class="showPassword ? 'pi pi-eye-slash' : 'pi pi-eye'"></i>
                            </button>
                        </div>
                    </div>
                    <div class="input-group">
                        <label>Konfirmasi Sandi</label>
                        <div class="input-with-icon">
                            <input v-model="daftarForm.password2" :type="showPassword2 ? 'text' : 'password'" required
                                minlength="10" placeholder="Ketik ulang sandi" class="form-input"
                                :disabled="sedangProses" />
                            <button type="button" class="btn-toggle" @click="showPassword2 = !showPassword2"
                                tabindex="-1">
                                <i :class="showPassword2 ? 'pi pi-eye-slash' : 'pi pi-eye'"></i>
                            </button>
                        </div>
                    </div>
                </div>

                <button type="submit" class="btn-submit" :disabled="sedangProses">
                    <i v-if="sedangProses" class="pi pi-spin pi-spinner"></i>
                    <span>{{ sedangProses ? 'Memproses Data...' : 'Kirim Pendaftaran' }}</span>
                </button>

                <div class="footer-links">
                    <span class="text-muted">Sudah punya akun?</span>
                    <router-link to="/login" class="link-primary">Login di sini</router-link>
                </div>
            </form>
        </div>
    </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useAuth } from '@/composables/useAuth'

const { register, sedangProses } = useAuth()

const daftarForm = reactive({
    nama_lengkap: '',
    username: '',
    email: '',
    telepon: '',
    password: '',
    password2: ''
})

const showPassword = ref(false)
const showPassword2 = ref(false)
const sukses = ref('')
const pesan = ref('')

const handleDaftar = async () => {
    pesan.value = ''
    sukses.value = ''

    if (daftarForm.password.length < 10) {
        pesan.value = 'Kata Sandi terlalu pendek. Masukkan minimal 10 karakter.'
        return
    }

    if (daftarForm.password !== daftarForm.password2) {
        pesan.value = 'Kata Sandi dan Konfirmasi Kata Sandi tidak cocok.'
        return
    }

    const hasil = await register({ ...daftarForm })

    if (!hasil.success) {
        pesan.value = hasil.message
        return
    }

    sukses.value = 'Pendaftaran berhasil dikirim. Akun Anda dapat digunakan setelah disetujui oleh Supervisor.'
    Object.assign(daftarForm, {
        nama_lengkap: '', username: '', email: '',
        telepon: '', password: '', password2: '',
    })
}
</script>

<style scoped>
* {
    box-sizing: border-box;
}

.register-wrapper {
    display: flex;
    min-height: 100vh;
    width: 100%;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    padding: 2rem 1rem;
    color: #1e293b;
}

.register-box {
    background: #ffffff;
    width: 100%;
    max-width: 520px;
    padding: 2.5rem;
    border-radius: 1.25rem;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.05), 0 1px 3px rgba(0, 0, 0, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.5);
    position: relative;
    overflow: hidden;
}

.header {
    text-align: center;
    margin-bottom: 2rem;
}

.icon-wrap {
    width: 3.5rem;
    height: 3.5rem;
    background: #f0fdfa;
    color: #0d9488;
    border-radius: 1rem;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
    margin: 0 auto 1rem auto;
    box-shadow: 0 4px 14px rgba(13, 148, 136, 0.1);
}

.title {
    font-size: 1.5rem;
    font-weight: 700;
    color: #0f172a;
    margin: 0 0 0.5rem 0;
    letter-spacing: -0.025em;
}

.subtitle {
    font-size: 0.9375rem;
    color: #64748b;
    margin: 0;
    line-height: 1.5;
}


.register-form {
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
}

.form-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 1.25rem;
}

@media (min-width: 480px) {
    .form-grid {
        grid-template-columns: 1fr 1fr;
        gap: 1rem;
    }
}

.input-group {
    display: flex;
    flex-direction: column;
    gap: 0.375rem;
}

.input-group label {
    font-size: 0.875rem;
    font-weight: 600;
    color: #334155;
}

.input-with-icon {
    position: relative;
    display: flex;
    align-items: center;
}

.form-input {
    width: 100%;
    border-radius: 0.5rem;
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    padding: 0.75rem 1rem;
    font-size: 0.9375rem;
    color: #1e293b;
    transition: all 0.2s ease;
    outline: none;
    font-family: inherit;
}

.form-input::placeholder {
    color: #94a3b8;
}

.form-input:focus {
    background: #ffffff;
    border-color: #14b8a6;
    box-shadow: 0 0 0 4px rgba(20, 184, 166, 0.1);
}

.form-input:disabled {
    background: #f1f5f9;
    color: #94a3b8;
    cursor: not-allowed;
}

.input-with-icon .form-input {
    padding-right: 2.75rem;
}

.btn-toggle {
    position: absolute;
    right: 0.75rem;
    background: none;
    border: none;
    color: #94a3b8;
    cursor: pointer;
    padding: 0.25rem;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: color 0.2s;
}

.btn-toggle:hover {
    color: #0f172a;
}

.btn-submit {
    width: 100%;
    background: linear-gradient(to right, #0f766e, #0d9488);
    color: #ffffff;
    border: none;
    border-radius: 0.5rem;
    padding: 0.875rem;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 0.5rem;
    margin-top: 0.5rem;
    box-shadow: 0 4px 12px rgba(13, 148, 136, 0.2);
}

.btn-submit:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 6px 16px rgba(13, 148, 136, 0.3);
}

.btn-submit:active:not(:disabled) {
    transform: translateY(0);
}

.btn-submit:disabled {
    background: #94a3b8;
    box-shadow: none;
    cursor: not-allowed;
    opacity: 0.8;
}

.alert {
    padding: 1rem;
    border-radius: 0.5rem;
    font-size: 0.875rem;
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    line-height: 1.5;
}

.alert-error {
    background: #fef2f2;
    border: 1px solid #fecaca;
    color: #b91c1c;
}

.alert-error i {
    color: #ef4444;
    font-size: 1.125rem;
    margin-top: 0.125rem;
}

.alert-success {
    background: #f0fdfa;
    border: 1px solid #ccfbf1;
    color: #0f766e;
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding: 2.5rem 1.5rem;
}

.alert-success .icon-large {
    font-size: 3.5rem;
    color: #14b8a6;
    margin-bottom: 0.5rem;
}

.alert-success h3 {
    font-size: 1.125rem;
    margin: 0 0 0.5rem 0;
    color: #115e59;
}

.alert-success p {
    margin: 0 0 1.5rem 0;
    color: #0f766e;
}

.link-back-success {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    background: #ffffff;
    color: #0d9488;
    padding: 0.5rem 1rem;
    border-radius: 2rem;
    text-decoration: none;
    font-weight: 600;
    border: 1px solid #99f6e4;
    transition: all 0.2s;
}

.link-back-success:hover {
    background: #f0fdfa;
    border-color: #5eead4;
}

.footer-links {
    text-align: center;
    margin-top: 1rem;
    font-size: 0.875rem;
}

.text-muted {
    color: #64748b;
    margin-right: 0.375rem;
}

.link-primary {
    color: #0d9488;
    font-weight: 600;
    text-decoration: none;
    transition: color 0.2s;
}

.link-primary:hover {
    color: #0f766e;
    text-decoration: underline;
}

.animate-fade-in {
    animation: fadeIn 0.4s ease-out forwards;
}

@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(15px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}
</style>