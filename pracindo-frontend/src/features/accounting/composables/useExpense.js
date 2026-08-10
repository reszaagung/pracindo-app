import { ref } from 'vue';
import api from '@/utils/api'

export function useExpense() {
  const daftarBelanja = ref([]);
  const daftarAkunKas = ref([]);   // Untuk Sumber Dana (Aset)
  const daftarAkunBeban = ref([]); // Untuk Kategori (Beban)
  const isLoading = ref(false);
  const error = ref(null);

  // Tarik data COA dari Backend
  const fetchDaftarAkun = async () => {
    try {
      const response = await api.get('akunting/akun/');
      let semuaAkun = response.data?.results || response.data?.data || response.data || [];

      // Filter otomatis: Hanya ambil akun yang Boleh Diposting
      daftarAkunKas.value = semuaAkun.filter(a => a.tipe.toLowerCase() === 'aset' && a.boleh_diposting);
      daftarAkunBeban.value = semuaAkun.filter(a => a.tipe.toLowerCase() === 'beban' && a.boleh_diposting);
    } catch (err) {
      console.error("Gagal mengambil master akun COA:", err);
    }
  };

  const fetchSemuaBelanja = async (entitasId = 1) => {
    isLoading.value = true;
    error.value = null;
    try {
      const response = await api.get('akunting/pengeluaran-kas/', {
        params: { entitas: entitasId }
      });
      let data = response.data?.results || response.data?.data || response.data || [];
      if (!Array.isArray(data)) data = [data];

      daftarBelanja.value = data.sort((a, b) => new Date(b.tanggal) - new Date(a.tanggal));
    } catch (err) {
      console.error("Gagal mengambil data pengeluaran:", err);
      error.value = "Gagal memuat data pengeluaran dari server.";
    } finally {
      isLoading.value = false;
    }
  };

  const tambahPengeluaran = async (payload) => {
    const formData = new FormData();

    // Mapping disesuaikan 100% dengan field di model PengeluaranKas
    formData.append('entitas', payload.entitas);
    formData.append('sumber_dana', payload.sumber_dana);
    formData.append('kategori_beban', payload.kategori_beban);
    formData.append('keterangan', payload.keterangan);
    formData.append('pemohon', payload.pemohon);
    formData.append('nominal', payload.nominal);

    if (payload.dokumen instanceof File) {
      formData.append('dokumen', payload.dokumen);
    }

    try {
      const response = await api.post('akunting/pengeluaran-kas/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      await fetchSemuaBelanja(payload.entitas);

      // Otomatis trigger endpoint posting agar jurnal tercetak
      const idBaru = response.data.id;
      if (idBaru) {
        await api.post(`akunting/pengeluaran-kas/${idBaru}/posting/`);
      }

      return { success: true, data: response.data };
    } catch (err) {
      console.error("Error dari server:", err.response?.data);
      return {
        success: false,
        message: err.response?.data?.detail || err.response?.data?.message || "Terjadi kesalahan saat menyimpan data."
      };
    }
  };

  return {
    daftarBelanja,
    daftarAkunKas,
    daftarAkunBeban,
    isLoading,
    error,
    fetchDaftarAkun,
    fetchSemuaBelanja,
    tambahPengeluaran
  };
}