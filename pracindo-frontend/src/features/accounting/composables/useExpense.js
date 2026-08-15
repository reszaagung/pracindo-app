import { ref } from 'vue';
import api from '@/utils/api'

export function useExpense() {
  const daftarBelanja = ref([]);
  const daftarAkunKas = ref([]);
  const daftarAkunBeban = ref([]);
  const daftarEntitas = ref([]); 
  const isLoading = ref(false);
  const error = ref(null);

  const fetchEntitas = async () => {
    try {
      const response = await api.get('auth/portal/');
      daftarEntitas.value = response.data?.entitas || response.data?.results || response.data || [];
    } catch (err) {
      console.error("Gagal memuat data entitas:", err);
    }
  };

  const fetchDaftarAkun = async () => {
    try {
      const response = await api.get('akunting/akun/');
      let semuaAkun = response.data?.results || response.data?.data || response.data || [];
      daftarAkunKas.value = semuaAkun.filter(a => a.tipe.toLowerCase() === 'aset' && a.boleh_diposting);
      daftarAkunBeban.value = semuaAkun.filter(a => a.tipe.toLowerCase() === 'beban' && a.boleh_diposting);
    } catch (err) {
      console.error("Gagal mengambil master akun COA:", err);
    }
  };

  const fetchSemuaBelanja = async (entitasId) => {
    if (!entitasId) return; 

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
      console.error("Gagal mengambil data pengeluaran:", err.response?.data || err.message);
      error.value = "Gagal memuat data pengeluaran dari server.";
    } finally {
      isLoading.value = false;
    }
  };

  const tambahPengeluaran = async (payload) => {
    const formData = new FormData();
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

      const idBaru = response.data.id;
      if (idBaru) {
        await api.post(`akunting/pengeluaran-kas/${idBaru}/posting/`);
      }

      return { success: true, data: response.data };
    } catch (err) {
      console.error("Error dari server:", err.response?.data);
      let pesanError = "Terjadi kesalahan saat menyimpan data.";
      if (err.response?.data) {
        if (typeof err.response.data === 'string') pesanError = err.response.data;
        else if (err.response.data.detail) pesanError = err.response.data.detail;
        else if (err.response.data.message) pesanError = err.response.data.message;
        else pesanError = JSON.stringify(err.response.data); 
      }

      return { success: false, message: pesanError };
    }
  };

  return {
    daftarBelanja, daftarAkunKas, daftarAkunBeban, daftarEntitas,
    isLoading, error, fetchEntitas, fetchDaftarAkun, fetchSemuaBelanja, tambahPengeluaran
  };
}