import { ref, reactive, computed, watch, onMounted } from 'vue'
import { apiTangki, apiBatch, apiPratinjau, apiRawUntukProduksi } from '../api'

const JENIS = {
  MIXING: 'MIXING',
  BLENDING: 'BLENDING'
}

export function useInputProduksi() {
  const mode = ref('list')
  const jenisProduksi = ref(JENIS.MIXING)
  const editingBatchId = ref(null)
  const loadingList = ref(false)
  const loadingForm = ref(false)
  const submitting = ref(false)
  const errorMsg = ref('')
  const daftarTangki = ref([])
  const daftarRaw = ref([])
  const daftarBatch = ref([])

  const filter = reactive({
    jenis: '',
    tangki: '',
    search: ''
  })

  const form = reactive({
    nama_hasil: '',
    tangki_tujuan: '',
    batch: '',
    tekor_kg: 0
  })

  const bomRows = ref([])
  const wipRows = ref([])
  const pratinjau = ref(null)

  let seqBom = 0
  function buatBarisBom() {
    seqBom += 1
    return { _id: `bom-${seqBom}`, raw: '', qty: 0, saldo: 0, harga: 0, subtotal: 0 }
  }

  let seqWip = 0
  function buatBarisWip() {
    seqWip += 1
    return { _id: `wip-${seqWip}`, tangki_asal: '', batch: '', qty: 0, tersedia: 0, harga: 0, opsiBatch: [] }
  }

  async function muatTangki() {
    try {
      const res = await apiTangki.daftar()
      daftarTangki.value = res?.results ?? res ?? []
    } catch {
      errorMsg.value = 'Gagal memuat daftar tangki'
    }
  }

  async function muatRawPool() {
    try {
      const res = await apiRawUntukProduksi.daftar()
      const list = res?.rincian ?? res?.data?.rincian ?? res?.results ?? res ?? []
      daftarRaw.value = list
        .filter((item) => Number(item.qty_kg) > 0)
        .map((item) => ({ ...item, raw: item.produk_id }))
    } catch {
      errorMsg.value = 'Gagal memuat saldo bahan baku'
    }
  }

  async function muatDaftarBatch() {
    loadingList.value = true
    try {
      const params = {}
      if (filter.jenis) params.jenis = filter.jenis
      if (filter.tangki) params.tangki = filter.tangki
      if (filter.search) params.search = filter.search
      const res = await apiBatch.daftar(params)
      daftarBatch.value = res?.results ?? res ?? []
    } catch {
      errorMsg.value = 'Gagal memuat daftar batch produksi'
    } finally {
      loadingList.value = false
    }
  }

  async function muatBatchTersediaUntukTangki(tangkiId) {
    if (!tangkiId) return []
    try {
      const res = await apiBatch.tersedia(tangkiId)
      return res?.results ?? res ?? []
    } catch {
      errorMsg.value = 'Gagal memuat batch WIP tersedia'
      return []
    }
  }

  async function initHalaman() {
    await Promise.all([muatTangki(), muatDaftarBatch()])
  }

  async function bukaFormBaru(jenis = JENIS.MIXING) {
    resetForm()
    jenisProduksi.value = jenis
    editingBatchId.value = null
    mode.value = 'form'
    loadingForm.value = true
    await muatRawPool()
    bomRows.value = [buatBarisBom()]
    wipRows.value = jenis === JENIS.BLENDING ? [buatBarisWip()] : []
    loadingForm.value = false
  }

  async function bukaFormEdit(batchId) {
    editingBatchId.value = batchId
    mode.value = 'form'
    loadingForm.value = true
    errorMsg.value = ''
    try {
      const [detail, komposisi] = await Promise.all([
        apiBatch.detail(batchId),
        apiBatch.komposisi(batchId)
      ])
      jenisProduksi.value = detail.jenis || JENIS.MIXING
      form.nama_hasil = detail.nama_hasil || ''
      form.tangki_tujuan = detail.tangki_tujuan || detail.tangki || ''
      form.batch = detail.batch || detail.nomor_batch || ''
      form.tekor_kg = Number(detail.tekor_kg || 0)

      await muatRawPool()

      bomRows.value = (komposisi?.materials || komposisi?.bahan_baku || []).map((m) => {
        const row = buatBarisBom()
        row.raw = m.raw
        row.qty = Number(m.qty_kg)
        row.harga = Number(m.harga_per_kg)
        row.subtotal = row.qty * row.harga
        perbaruiTelemetriBom(row)
        return row
      })
      if (bomRows.value.length === 0) bomRows.value = [buatBarisBom()]

      if (jenisProduksi.value === JENIS.BLENDING) {
        const wipSources = komposisi?.wip_sources || komposisi?.info_blending || []
        wipRows.value = await Promise.all(
          wipSources.map(async (w) => {
            const row = buatBarisWip()
            row.tangki_asal = w.tangki_asal
            row.opsiBatch = await muatBatchTersediaUntukTangki(w.tangki_asal)
            row.batch = w.batch
            row.qty = Number(w.qty_kg)
            const opsi = row.opsiBatch.find((b) => b.batch === row.batch)
            row.tersedia = Number(opsi?.sisa_qty ?? opsi?.saldo_qty ?? 0)
            row.harga = Number(opsi?.harga_per_kg ?? w.harga_per_kg ?? 0)
            return row
          })
        )
        if (wipRows.value.length === 0) wipRows.value = [buatBarisWip()]
      } else {
        wipRows.value = []
      }
      pratinjau.value = null
    } catch {
      errorMsg.value = 'Gagal memuat detail batch'
    } finally {
      loadingForm.value = false
    }
  }

  function tutupForm() {
    mode.value = 'list'
    resetForm()
  }

  function resetForm() {
    form.nama_hasil = ''
    form.tangki_tujuan = ''
    form.batch = ''
    form.tekor_kg = 0
    bomRows.value = []
    wipRows.value = []
    pratinjau.value = null
    errorMsg.value = ''
  }

  function gantiJenisProduksi(jenis) {
    if (editingBatchId.value) return
    jenisProduksi.value = jenis
    bomRows.value = [buatBarisBom()]
    wipRows.value = jenis === JENIS.BLENDING ? [buatBarisWip()] : []
    pratinjau.value = null
  }

  async function tambahTangkiBaru(nama) {
    const namaBersih = String(nama || '').trim().toUpperCase()
    if (!namaBersih) return null
    const existing = daftarTangki.value.find(
      (t) => (t.nama || t.kode || '').toUpperCase() === namaBersih
    )
    if (existing) return existing
    try {
      const dibuat = await apiTangki.buat({ nama: namaBersih, kode: namaBersih })
      await muatTangki()
      return dibuat
    } catch {
      errorMsg.value = 'Gagal membuat tangki baru'
      return null
    }
  }

  async function generateNomorBatch() {
    try {
      const res = await apiBatch.nomorBaru(jenisProduksi.value)
      form.batch = res?.nomor ?? res?.batch ?? ''
    } catch {
      errorMsg.value = 'Gagal membuat nomor batch otomatis'
    }
  }

  function tambahBomRow() { bomRows.value.push(buatBarisBom()) }

  function hapusBomRow(id) {
    if (bomRows.value.length <= 1) return
    bomRows.value = bomRows.value.filter((r) => r._id !== id)
  }

  function perbaruiTelemetriBom(row) {
    const item = daftarRaw.value.find((r) => r.raw === row.raw)
    row.saldo = item ? Number(item.qty_kg) : 0
    row.harga = item ? Number(item.harga_rata) : 0
    row.subtotal = (Number(row.qty) || 0) * row.harga
  }

  function tambahWipRow() { wipRows.value.push(buatBarisWip()) }

  function hapusWipRow(id) {
    wipRows.value = wipRows.value.filter((r) => r._id !== id)
  }

  async function saatTangkiAsalDipilih(row) {
    row.batch = ''
    row.tersedia = 0
    row.harga = 0
    row.opsiBatch = await muatBatchTersediaUntukTangki(row.tangki_asal)
  }

  function saatBatchWipDipilih(row) {
    const opsi = row.opsiBatch.find((b) => b.batch === row.batch)
    row.tersedia = opsi ? Number(opsi.sisa_qty ?? opsi.saldo_qty ?? 0) : 0
    row.harga = opsi ? Number(opsi.harga_per_kg ?? 0) : 0
  }

  const totalQtyBom = computed(() => bomRows.value.reduce((s, r) => s + (Number(r.qty) || 0), 0))
  const totalNilaiBom = computed(() => bomRows.value.reduce((s, r) => s + (Number(r.qty) || 0) * (Number(r.harga) || 0), 0))
  const totalQtyWip = computed(() => jenisProduksi.value === JENIS.BLENDING ? wipRows.value.reduce((s, r) => s + (Number(r.qty) || 0), 0) : 0)
  const totalNilaiWip = computed(() => jenisProduksi.value === JENIS.BLENDING ? wipRows.value.reduce((s, r) => s + (Number(r.qty) || 0) * (Number(r.harga) || 0), 0) : 0)
  const totalInputKg = computed(() => totalQtyBom.value + totalQtyWip.value)
  const totalInputNilai = computed(() => totalNilaiBom.value + totalNilaiWip.value)
  const proyeksiYield = computed(() => totalInputKg.value - (Number(form.tekor_kg) || 0))
  const proyeksiHargaRata = computed(() => proyeksiYield.value > 0 ? totalInputNilai.value / proyeksiYield.value : 0)

  function susunPayload() {
    const payload = {
      nama_hasil: form.nama_hasil.trim(),
      tangki_tujuan: Number(form.tangki_tujuan),
      batch: form.batch.trim(),
      tekor_kg: Number(form.tekor_kg) || 0,
      materials: bomRows.value
        .filter((r) => r.raw && Number(r.qty) > 0)
        .map((r) => ({ raw: String(r.raw), qty_kg: Number(r.qty) })),
      wip_sources: []
    }

    if (jenisProduksi.value === JENIS.BLENDING) {
      payload.wip_sources = wipRows.value
        .filter((r) => r.batch && Number(r.qty) > 0)
        .map((r) => ({
          tangki_asal: Number(r.tangki_asal),
          batch: String(r.batch),
          qty_kg: Number(r.qty)
        }))
    }
    return payload
  }

  function validasiForm() {
    if (!form.nama_hasil.trim()) return 'Nama hasil produksi wajib diisi'
    if (!form.tangki_tujuan) return 'Tangki tujuan wajib dipilih'
    if (!form.batch.trim()) return 'Batch ID wajib diisi'

    const adaBom = bomRows.value.some((r) => r.raw && Number(r.qty) > 0)
    const adaWip = jenisProduksi.value === JENIS.BLENDING && wipRows.value.some((r) => r.batch && Number(r.qty) > 0)

    if (jenisProduksi.value === JENIS.MIXING && !adaBom) {
      return 'Minimal satu baris bahan baku (BOM) harus diisi'
    }
    if (jenisProduksi.value === JENIS.BLENDING && !adaBom && !adaWip) {
      return 'Minimal satu sumber WIP atau bahan baku harus diisi'
    }

    for (const row of bomRows.value) {
      if (row.raw && Number(row.qty) > row.saldo + 0.001) {
        return `Saldo pool tidak cukup. Diminta ${row.qty} Kg, tersedia ${row.saldo.toFixed(3)} Kg`
      }
    }

    if (jenisProduksi.value === JENIS.BLENDING) {
      for (const row of wipRows.value) {
        if (row.batch && Number(row.qty) > row.tersedia + 0.001) {
          return `Saldo WIP tidak cukup untuk batch`
        }
      }
    }

    if (proyeksiYield.value <= 0) {
      return 'Yield harus positif setelah dikurangi tekor/shrinkage'
    }
    return ''
  }

  async function mintaPratinjau() {
    errorMsg.value = validasiForm()
    if (errorMsg.value) return null
    try {
      const res = await apiPratinjau(susunPayload())
      pratinjau.value = res
      if (res && res.valid === false) {
        errorMsg.value = res.galat?.map(g => g.pesan).join(' | ') || 'Kalkulasi ditolak server.'
      }
      return res
    } catch (e) {
      errorMsg.value = e?.response?.data?.pesan || 'Gagal terhubung ke server untuk kalkulasi.'
      return null
    }
  }

  async function simpanDanPosting() {
    errorMsg.value = validasiForm()
    if (errorMsg.value) return false
    submitting.value = true
    try {
      const payload = susunPayload()
      if (editingBatchId.value) {
        await apiBatch.ubah(editingBatchId.value, payload)
      } else {
        await apiBatch.buat(payload)
      }
      
      // Karena backend sudah auto-posting pada saat 'buat' atau 'ubah',
      // kita tidak perlu lagi memanggil endpoint apiBatch.posting().
      // Langsung refresh data dan tutup form.
      await Promise.all([muatDaftarBatch(), muatRawPool()])
      tutupForm()
      return true
    } catch (e) {
      const data = e?.response?.data
      errorMsg.value = data?.detail || data?.pesan || e.message || (typeof data === 'object' ? Object.values(data)[0] : 'Gagal menyimpan batch produksi')
      return false
    } finally {
      submitting.value = false
    }
  }

  watch(
    bomRows,
    (rows) => rows.forEach((r) => (r.subtotal = (Number(r.qty) || 0) * (Number(r.harga) || 0))),
    { deep: true }
  )

  onMounted(() => {
    initHalaman()
  })

  return {
    JENIS,
    mode,
    jenisProduksi,
    editingBatchId,
    loadingList,
    loadingForm,
    submitting,
    errorMsg,
    daftarTangki,
    daftarRaw,
    daftarBatch,
    filter,
    form,
    bomRows,
    wipRows,
    pratinjau,
    totalQtyBom,
    totalNilaiBom,
    totalQtyWip,
    totalNilaiWip,
    totalInputKg,
    totalInputNilai,
    proyeksiYield,
    proyeksiHargaRata,
    muatDaftarBatch,
    bukaFormBaru,
    bukaFormEdit,
    tutupForm,
    gantiJenisProduksi,
    tambahTangkiBaru,
    generateNomorBatch,
    tambahBomRow,
    hapusBomRow,
    perbaruiTelemetriBom,
    tambahWipRow,
    hapusWipRow,
    saatTangkiAsalDipilih,
    saatBatchWipDipilih,
    mintaPratinjau,
    simpanDanPosting
  }
}