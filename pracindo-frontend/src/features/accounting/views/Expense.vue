<script setup>
import { onMounted, ref, reactive } from 'vue';
import { useExpense } from '@/features/accounting/composables/useExpense';

const {
  daftarBelanja, daftarAkunKas, daftarAkunBeban,
  isLoading, error, fetchDaftarAkun, fetchSemuaBelanja, tambahPengeluaran
} = useExpense();

const showModalTambah = ref(false);
const isSubmitting = ref(false);

const form = reactive({
  entitas: 1, // Default ID PT (Sesuaikan dengan ID di database Anda jika berbeda)
  sumber_dana: '',
  kategori_beban: '',
  keterangan: '',
  pemohon: '',
  nominal: '',
  dokumen: null
});

onMounted(async () => {
  await fetchDaftarAkun();
  await fetchSemuaBelanja(form.entitas);
});

const formatRupiah = (angka) => {
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    minimumFractionDigits: 0
  }).format(angka);
};

// Memberikan warna badge acak/tetap berdasarkan nama kategori beban
const getCategoryBadge = (kategoriNama) => {
  const name = String(kategoriNama || '').toUpperCase();
  if (name.includes('OPERASIONAL') || name.includes('TRANSPORTASI')) return 'bg-blue-50 text-blue-700 border-blue-200';
  if (name.includes('KONSUMSI')) return 'bg-amber-50 text-amber-700 border-amber-200';
  if (name.includes('PEMELIHARAAN') || name.includes('MAINTENANCE')) return 'bg-rose-50 text-rose-700 border-rose-200';
  if (name.includes('ATK') || name.includes('TULIS')) return 'bg-purple-50 text-purple-700 border-purple-200';
  return 'bg-slate-100 text-slate-700 border-slate-200';
};

const handleFileChange = (e) => {
  form.dokumen = e.target.files[0];
};

const handleSimpan = async () => {
  if (!form.sumber_dana || !form.kategori_beban || !form.keterangan || !form.nominal || !form.pemohon) {
    alert('Harap lengkapi field wajib dan pilih akun sumber dana/beban!');
    return;
  }

  isSubmitting.value = true;

  const result = await tambahPengeluaran(form);

  if (result.success) {
    alert("Data pengeluaran berhasil dicatat dan dijurnal secara otomatis!");
    showModalTambah.value = false;

    // Reset form state
    form.sumber_dana = '';
    form.kategori_beban = '';
    form.keterangan = '';
    form.nominal = '';
    form.pemohon = '';
    form.dokumen = null;
  } else {
    alert(result.message || 'Gagal menyimpan data.');
  }

  isSubmitting.value = false;
};
</script>

<template>
  <div class="space-y-6 animate-fade-in text-slate-700 p-2 sm:p-4 w-full overflow-hidden max-w-full">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
      <div>
        <h2 class="text-xl sm:text-2xl font-bold text-slate-800 tracking-tight flex items-center gap-2">
          <i class="pi pi-wallet text-emerald-600"></i> Kas Kecil (Petty Cash)
        </h2>
        <p class="text-slate-500 text-xs sm:text-sm mt-1">Kelola pencatatan pengeluaran operasional dan logistik.</p>
      </div>

      <button @click="showModalTambah = true"
        class="w-full sm:w-auto justify-center px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-bold rounded-xl shadow-sm transition-all flex items-center gap-2">
        <i class="pi pi-plus text-sm"></i>
        <span>Catat Pengeluaran</span>
      </button>
    </div>

    <!-- Error Alert -->
    <div v-if="error"
      class="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-xl flex items-center gap-3 shadow-sm">
      <i class="pi pi-exclamation-circle text-lg"></i>
      <span class="text-sm font-medium">{{ error }}</span>
    </div>

    <!-- Table Section -->
    <div class="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-sm w-full">
      <div class="overflow-x-auto custom-scrollbar pb-2">
        <table class="w-full text-left text-sm border-collapse whitespace-nowrap">
          <thead class="bg-slate-50 text-slate-500 border-b border-slate-200">
            <tr>
              <th class="py-4 px-4 sm:px-6 font-semibold">Tanggal & Bukti</th>
              <th class="py-4 px-3 sm:px-4 font-semibold text-center">Entitas</th>
              <th class="py-4 px-3 sm:px-4 font-semibold text-center">Kategori Beban</th>
              <th class="py-4 px-3 sm:px-4 font-semibold min-w-[200px]">Keterangan & Sumber Dana</th>
              <th class="py-4 px-3 sm:px-4 font-semibold">Pemohon</th>
              <th class="py-4 px-4 sm:px-6 font-semibold text-right">Nominal</th>
              <th class="py-4 px-3 sm:px-4 font-semibold text-center">Nota</th>
            </tr>
          </thead>

          <tbody v-if="isLoading && daftarBelanja.length === 0" class="divide-y divide-slate-100">
            <tr>
              <td colspan="7" class="py-10 text-center text-slate-400">
                <i class="pi pi-spin pi-spinner text-2xl mb-2 text-emerald-500"></i>
                <p class="text-sm font-medium">Memuat data brankas...</p>
              </td>
            </tr>
          </tbody>

          <tbody v-else class="divide-y divide-slate-100 bg-white">
            <tr v-if="daftarBelanja.length === 0">
              <td colspan="7" class="py-12 text-center text-slate-400">
                <div
                  class="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center mx-auto mb-3 border border-slate-100">
                  <i class="pi pi-inbox text-2xl text-slate-300"></i>
                </div>
                <p class="text-sm font-bold text-slate-500">Belum ada riwayat pengeluaran.</p>
                <p class="text-xs mt-1">Catat pengeluaran baru menggunakan tombol di atas.</p>
              </td>
            </tr>

            <template v-else>
              <tr v-for="(item, index) in daftarBelanja" :key="item.id || index"
                class="hover:bg-slate-50/80 transition-colors group">
                <td class="py-4 px-4 sm:px-6">
                  <span class="font-bold text-slate-700 block">{{ item.nomor_bukti || 'DRAFT' }}</span>
                  <span class="text-[11px] font-medium text-slate-500 flex items-center gap-1 mt-0.5">
                    <i class="pi pi-calendar text-[10px]"></i>
                    {{ new Date(item.tanggal || Date.now()).toLocaleDateString('id-ID', {
                      day: '2-digit', month: 'short', year: 'numeric'
                    }) }}
                  </span>
                </td>

                <td class="py-4 px-3 sm:px-4 text-center">
                  <span
                    :class="item.entitas_kode === 'PT' ? 'bg-blue-100 text-blue-700 border-blue-200' : 'bg-purple-100 text-purple-700 border-purple-200'"
                    class="px-2.5 py-1 rounded-md text-[10px] font-bold uppercase tracking-wide border inline-block">
                    {{ item.entitas_kode || 'UMUM' }}
                  </span>
                </td>

                <td class="py-4 px-3 sm:px-4 text-center">
                  <span :class="getCategoryBadge(item.kategori_beban_nama)"
                    class="px-2.5 py-1.5 rounded-md text-[10px] font-bold uppercase tracking-wide border inline-block max-w-[150px] truncate"
                    :title="item.kategori_beban_nama">
                    {{ item.kategori_beban_nama || 'UMUM' }}
                  </span>
                </td>

                <td class="py-4 px-3 sm:px-4">
                  <span class="text-sm font-semibold text-slate-700">{{ item.keterangan }}</span>
                  <span class="text-[11px] block mt-0.5 text-slate-500">
                    <i class="pi pi-arrow-right text-[8px] mr-1"></i>{{ item.sumber_dana_nama || '-' }}
                  </span>
                </td>

                <td class="py-4 px-3 sm:px-4">
                  <div class="flex items-center gap-2">
                    <div
                      class="w-6 h-6 rounded-full bg-slate-100 flex items-center justify-center text-[10px] font-bold text-slate-500 border border-slate-200 uppercase shrink-0">
                      {{ (item.pemohon || 'NN').substring(0, 2) }}
                    </div>
                    <span class="text-xs font-semibold text-slate-600">{{ item.pemohon }}</span>
                  </div>
                </td>

                <td class="py-4 px-4 sm:px-6 text-right">
                  <span class="font-black text-slate-800 tracking-tight">{{ formatRupiah(item.nominal) }}</span>
                </td>

                <td class="py-4 px-3 sm:px-4 text-center">
                  <!-- Jika backend merender nested dokumen_url, sesuaikan propertinya (misal: item.dokumen_url) -->
                  <a v-if="item.dokumen" :href="item.dokumen" target="_blank"
                    class="inline-flex items-center justify-center w-8 h-8 rounded-lg bg-blue-50 text-blue-600 hover:bg-blue-600 hover:text-white transition-colors border border-blue-100"
                    title="Lihat Nota">
                    <i class="pi pi-link text-sm"></i>
                  </a>
                  <span v-else
                    class="inline-flex items-center justify-center w-8 h-8 rounded-lg bg-slate-50 text-slate-300 border border-slate-100"
                    title="Tidak ada Nota">
                    <i class="pi pi-minus text-xs"></i>
                  </span>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Modal Tambah Pengeluaran -->
    <div v-if="showModalTambah"
      class="fixed inset-0 z-[70] flex items-center justify-center bg-slate-900/40 backdrop-blur-sm p-4 animate-fade-in"
      @click.self="showModalTambah = false">
      <div
        class="bg-white w-full max-w-lg rounded-[24px] shadow-2xl border border-slate-100 overflow-hidden flex flex-col animate-fade-in-up max-h-[90vh]">
        <div class="px-5 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50/50 shrink-0">
          <h3 class="text-base font-bold text-slate-800">Catat Pengeluaran Baru</h3>
          <button @click="showModalTambah = false" class="text-slate-400 hover:text-red-500 transition-colors">
            <i class="pi pi-times text-lg"></i>
          </button>
        </div>

        <div class="p-5 sm:p-6 space-y-5 overflow-y-auto custom-scrollbar">

          <!-- Entitas -->
          <div class="flex flex-col gap-1.5 mb-1">
            <label class="text-xs font-bold text-slate-500 uppercase tracking-wide">Gunakan Dompet Entitas</label>
            <div class="flex gap-2 sm:gap-4">
              <label class="flex-1 cursor-pointer">
                <input type="radio" v-model="form.entitas" :value="1" @change="fetchSemuaBelanja(1)"
                  class="peer sr-only" />
                <div
                  class="p-2.5 sm:p-3 text-center rounded-xl border-2 border-slate-100 font-bold text-xs sm:text-sm text-slate-500 peer-checked:border-blue-500 peer-checked:bg-blue-50 peer-checked:text-blue-700 transition-all">
                  🏢 PT</div>
              </label>
              <label class="flex-1 cursor-pointer">
                <input type="radio" v-model="form.entitas" :value="2" @change="fetchSemuaBelanja(2)"
                  class="peer sr-only" />
                <div
                  class="p-2.5 sm:p-3 text-center rounded-xl border-2 border-slate-100 font-bold text-xs sm:text-sm text-slate-500 peer-checked:border-purple-500 peer-checked:bg-purple-50 peer-checked:text-purple-700 transition-all">
                  🏭 CV</div>
              </label>
            </div>
          </div>

          <!-- SUMBER DANA (ASET) -->
          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-bold text-slate-500 uppercase tracking-wide">Sumber Dana (Rekening/Kas)</label>
            <select v-model="form.sumber_dana"
              class="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:bg-white transition-colors text-slate-800">
              <option value="" disabled>Pilih dompet / rekening bank...</option>
              <option v-for="akun in daftarAkunKas" :key="akun.id" :value="akun.id">
                [{{ akun.kode }}] {{ akun.nama }}
              </option>
            </select>
          </div>

          <!-- KATEGORI (BEBAN) -->
          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-bold text-slate-500 uppercase tracking-wide">Kategori Beban</label>
            <select v-model="form.kategori_beban"
              class="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:bg-white transition-colors text-slate-800">
              <option value="" disabled>Pilih jenis pengeluaran...</option>
              <option v-for="akun in daftarAkunBeban" :key="akun.id" :value="akun.id">
                [{{ akun.kode }}] {{ akun.nama }}
              </option>
            </select>
          </div>

          <!-- KETERANGAN -->
          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-bold text-slate-500 uppercase tracking-wide">Keterangan</label>
            <input type="text" v-model="form.keterangan" placeholder="Contoh: Beli bensin mobil box..."
              class="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:bg-white transition-colors text-slate-800" />
          </div>

          <!-- NOMINAL & PEMOHON -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div class="flex flex-col gap-1.5">
              <label class="text-xs font-bold text-slate-500 uppercase tracking-wide">Nominal (Rp)</label>
              <input type="number" v-model="form.nominal" placeholder="0"
                class="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-black focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:bg-white transition-colors text-slate-800" />
            </div>
            <div class="flex flex-col gap-1.5">
              <label class="text-xs font-bold text-slate-500 uppercase tracking-wide">Nama Pemohon</label>
              <input type="text" v-model="form.pemohon" placeholder="Nama staf..."
                class="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:bg-white transition-colors text-slate-800" />
            </div>
          </div>

          <!-- FILE UPLOAD -->
          <div class="flex flex-col gap-1.5 pt-3 border-t border-slate-100">
            <label class="text-xs font-bold text-slate-500 uppercase tracking-wide">Upload Nota / Struk
              (Opsional)</label>
            <input type="file" @change="handleFileChange"
              class="w-full px-3 py-2 text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-bold file:bg-emerald-50 file:text-emerald-700 hover:file:bg-emerald-100 cursor-pointer" />
          </div>
        </div>

        <div class="px-5 py-4 border-t border-slate-100 flex justify-end gap-3 bg-slate-50/50 shrink-0">
          <button @click="showModalTambah = false" :disabled="isSubmitting"
            class="px-5 py-2.5 text-xs font-bold text-slate-600 bg-white border border-slate-200 rounded-xl hover:bg-slate-50 disabled:opacity-50 transition-colors">Batal</button>
          <button @click="handleSimpan" :disabled="isSubmitting"
            class="px-6 py-2.5 text-xs font-bold text-white bg-emerald-600 rounded-xl hover:bg-emerald-700 shadow-sm flex items-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed transition-all">
            <i v-if="isSubmitting" class="pi pi-spin pi-spinner text-xs"></i>
            {{ isSubmitting ? 'Menyimpan...' : 'Simpan Pengeluaran' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.animate-fade-in {
  animation: fadeIn 0.3s ease-out forwards;
}

.animate-fade-in-up {
  animation: fadeInUp 0.3s ease-out forwards;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }

  to {
    opacity: 1;
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(15px) scale(0.98);
  }

  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: #cbd5e1;
  border-radius: 10px;
}

.custom-scrollbar:hover::-webkit-scrollbar-thumb {
  background-color: #94a3b8;
}
</style>