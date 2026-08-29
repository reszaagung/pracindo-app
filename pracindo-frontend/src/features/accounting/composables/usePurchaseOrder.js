import { ref, computed } from 'vue'
import api from '@/utils/api'
import { bacaError } from '@/utils/error'
import { generateKode } from '@/utils/generate_id'

export function usePurchaseOrder() {
    const daftarPO = ref([])
    const isLoadingDaftar = ref(false)
    const cari = ref('')
    const saringStatus = ref('semua')

    const listEntitas = ref([])
    const listSupplier = ref([])
    const listSatuan = ref([])
    const sedangProses = ref(false)
    const pesanError = ref('')
    const previewNomor = ref('')

    const periodeDitutup = ref(false)

    const muatDaftarPO = async () => {
        isLoadingDaftar.value = true
        try {
            const { data } = await api.get('akunting/purchase-order/')
            daftarPO.value = data.results || data || []
        } catch (err) {
            console.error('Gagal memuat daftar PO:', bacaError(err))
        } finally {
            isLoadingDaftar.value = false
        }
    }

    const tampil = computed(() => {
            const q = cari.value.trim().toLowerCase()
            return daftarPO.value
                .filter(po => {
                    // PERBAIKAN 1: Samakan case (huruf kecil) agar filter tab berfungsi!
                    const statusFilter = saringStatus.value
                    if (statusFilter === 'semua') return true
                    return (po.status || '').toLowerCase() === statusFilter
                })
                .filter(po => !q
                    || (po.no_po || po.nomor || '').toLowerCase().includes(q)
                    || (po.suplier_nama || '').toLowerCase().includes(q))
                .sort((a, b) => {
                    // PERBAIKAN 2: Gunakan localeCompare untuk string tanggal (YYYY-MM-DD). Jauh lebih ringan dari new Date()!
                    return (b.tanggal || '').localeCompare(a.tanggal || '')
                })
        })

    const belumDiterima = computed(() =>
        daftarPO.value.filter(po => ['TERKIRIM', 'DISETUJUI', 'SEBAGIAN'].includes(po.status))
    )

    const draftCount = computed(() =>
        daftarPO.value.filter(po => po.status === 'DRAFT').length
    )

    const totalBulanIni = computed(() => {
        const kini = new Date()
        return daftarPO.value
            .filter(po => {
                const d = new Date(po.tanggal)
                return d.getMonth() === kini.getMonth() && d.getFullYear() === kini.getFullYear()
            })
            .reduce((s, po) => s + Number(po.total_nilai ?? 0), 0)
    })

    const muatDataMaster = async () => {
        sedangProses.value = true
        pesanError.value = ''
        try {
            const [resPortal, resSupplier] = await Promise.all([
                api.get('auth/portal/'),
                api.get('master/suplier/', { params: { ringkas: 1, aktif: true } })
            ])

            const pd = resPortal.data;
            listEntitas.value = pd?.entitas || pd?.data?.entitas || pd?.results || pd?.data || (Array.isArray(pd) ? pd : []);
            listSupplier.value = resSupplier.data?.results || resSupplier.data || [];

        } catch (err) {
            console.error("Gagal memuat master:", err)
            pesanError.value = bacaError(err, 'Gagal memuat data master (Entitas/Suplier).')
        } finally {
            sedangProses.value = false
        }
    }

    // Ditambahkan parameter `jenis` (default: 'BAHAN_BAKU')
    const muatPreviewNomor = async (entitasId, tanggal, jenis = 'BAHAN_BAKU') => {
        if (!entitasId || !tanggal) {
            previewNomor.value = 'Pilih entitas & tanggal'
            return
        }
        try {
            const { data } = await api.get('akunting/purchase-order/preview-nomor/', {
                params: { entitas: entitasId, tanggal, jenis }
            })
            previewNomor.value = data.nomor || 'TIDAK TERSEDIA'
        } catch {
            previewNomor.value = 'GAGAL MEMUAT NOMOR'
        }
    }

    const cekStatusPeriode = async (entitasId, tanggal) => {
        if (!entitasId || !tanggal) {
            periodeDitutup.value = false
            return
        }

        try {
            const { data } = await api.get('core/periode/status/', {
                params: { entitas: entitasId, tanggal }
            })
            periodeDitutup.value = !data.terbuka
            if (periodeDitutup.value) {
                pesanError.value = data.pesan || 'Periode akuntansi untuk entitas & tanggal ini sudah ditutup.'
            }
        } catch (err) {
            console.error('Gagal mengecek status periode:', err)
            periodeDitutup.value = false
        }
    }

    // Ditambahkan parameter `jenis` untuk menentukan Prefix dan Satuan Default
    const buatProdukBaru = async (nama, jenis = 'BAHAN_BAKU') => {
        const namaProduk = nama.trim()
        if (!namaProduk) throw new Error('Nama produk wajib diisi.')

        if (!listSatuan.value.length) {
            const { data } = await api.get('master/satuan/', { params: { aktif: true } })
            listSatuan.value = data.results || data || []
        }

        let satuanDefault = null
        if (jenis === 'KEMASAN') {
            satuanDefault = listSatuan.value.find(s => ['pcs', 'unit', 'pack'].includes(s.kode?.toLowerCase())) || listSatuan.value[0]
        } else {
            satuanDefault = listSatuan.value.find(s => s.kode?.toLowerCase() === 'kg') || listSatuan.value[0]
        }

        if (!satuanDefault) throw new Error('Belum ada data satuan pada master.')

        const prefix = jenis === 'KEMASAN' ? 'PK' : 'RM'
        const kode = generateKode(prefix)
        try {
            const { data } = await api.post('master/produk/', {
                kode, nama: namaProduk, jenis: jenis, satuan: satuanDefault.id
            })
            return {
                id: data.id, kode: data.kode, nama: data.nama,
                satuan_kode: data.satuan_kode, jenis: data.jenis
            }
        } catch (err) {
            throw new Error(bacaError(err, 'Gagal membuat produk baru.'), { cause: err })
        }
    }

    // Dimodifikasi agar membaca field kategori_po dan mem-parsing harga
    const simpanPO = async (form, isKirim = false) => {
        if (periodeDitutup.value) {
            pesanError.value = 'Tidak dapat menyimpan PO karena periode telah ditutup.'
            return { success: false, message: pesanError.value }
        }

        sedangProses.value = true
        pesanError.value = ''
        try {
            const payloadItems = form.items
                .filter(i => i.produk_id && parseFloat(i.qty_pesan) > 0)
                .map(i => ({
                    produk_id: i.produk_id,
                    qty_pesan: String(i.qty_pesan),
                    // Mendukung field harga_per_kg maupun harga_per_unit dari frontend
                    harga_per_kg: String(i.harga_per_kg ?? i.harga_per_unit ?? 0),
                    satuan: i.satuan || (form.kategori_po === 'KEMASAN' ? 'pcs' : 'kg'),
                }))

            if (!payloadItems.length) {
                pesanError.value = 'Minimal harus ada 1 item dengan produk dan Qty lebih dari 0.'
                return { success: false, message: pesanError.value }
            }

            const payload = {
                entitas_id: form.entitas_id,
                suplier_id: form.suplier_id,
                tanggal: form.tanggal,
                tanggal_kirim_diminta: form.tanggal_kirim_diminta || null,
                catatan: form.catatan,
                pakai_ppn: form.pakai_ppn,
                ppn_persen: form.ppn_persen || 11.00,
                kategori_po: form.kategori_po || 'BAHAN_BAKU', // Sisipkan kategori PO
                items: payloadItems
            }

            const res = await api.post('akunting/purchase-order/', payload)
            const idPO = res.data.id

            if (isKirim && idPO) {
                await api.post(`akunting/purchase-order/${idPO}/ajukan/`)
            }

            await muatDaftarPO()
            return { success: true, data: res.data }

        } catch (err) {
            pesanError.value = bacaError(err, 'Gagal menyimpan PO.')
            return { success: false, message: pesanError.value }
        } finally {
            sedangProses.value = false
        }
    }

    // ==========================================
    // ACTION PERUBAHAN STATUS (API ENDPOINTS)
    // ==========================================

    const ajukanPO = async (po_id) => {
        sedangProses.value = true
        pesanError.value = ''
        try {
            await api.post(`akunting/purchase-order/${po_id}/ajukan/`)
            await muatDaftarPO()
            return { success: true }
        } catch (err) {
            pesanError.value = bacaError(err, 'Gagal mengajukan PO.')
            return { success: false, message: pesanError.value }
        } finally {
            sedangProses.value = false
        }
    }

    const setujuiPO = async (po_id) => {
        sedangProses.value = true
        pesanError.value = ''
        try {
            await api.post(`akunting/purchase-order/${po_id}/setujui/`)
            await muatDaftarPO()
            return { success: true }
        } catch (err) {
            pesanError.value = bacaError(err, 'Gagal menyetujui PO.')
            return { success: false, message: pesanError.value }
        } finally {
            sedangProses.value = false
        }
    }

    const tolakPO = async (po_id, alasan) => {
        sedangProses.value = true
        pesanError.value = ''
        try {
            await api.post(`akunting/purchase-order/${po_id}/tolak/`, { alasan })
            await muatDaftarPO()
            return { success: true }
        } catch (err) {
            pesanError.value = bacaError(err, 'Gagal menolak PO.')
            return { success: false, message: pesanError.value }
        } finally {
            sedangProses.value = false
        }
    }

    const kirimPO = async (po_id) => {
        sedangProses.value = true
        pesanError.value = ''
        try {
            await api.post(`akunting/purchase-order/${po_id}/kirim/`)
            await muatDaftarPO()
            return { success: true }
        } catch (err) {
            pesanError.value = bacaError(err, 'Gagal mengirim PO ke Suplier.')
            return { success: false, message: pesanError.value }
        } finally {
            sedangProses.value = false
        }
    }

    const batalkanPO = async (po_id, alasan) => {
        sedangProses.value = true
        pesanError.value = ''
        try {
            await api.post(`akunting/purchase-order/${po_id}/batalkan/`, { alasan })
            await muatDaftarPO()
            return { success: true }
        } catch (err) {
            pesanError.value = bacaError(err, 'Gagal membatalkan PO.')
            return { success: false, message: pesanError.value }
        } finally {
            sedangProses.value = false
        }
    }

    return {
        daftarPO, isLoadingDaftar, cari, saringStatus, tampil,
        belumDiterima, draftCount, totalBulanIni, muatDaftarPO,
        listEntitas, listSupplier, sedangProses,
        pesanError, previewNomor, muatDataMaster, muatPreviewNomor,
        buatProdukBaru, simpanPO,
        periodeDitutup, cekStatusPeriode,
        ajukanPO, setujuiPO, tolakPO, kirimPO, batalkanPO
    }
}
