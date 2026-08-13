import { ref, reactive, computed, onMounted } from 'vue'
import api from '@/utils/api'
import { statusTagihan } from '@/utils/format'

export function useDocument() {
    const isLoading = ref(false)
    const searchQuery = ref('')
    const statusFilter = ref('all')
    const uploadForm = reactive({
        po_reference: '',
        document_type: 'Invoice',
        document_number: '',
        partner_name: '',
        upload_date: new Date().toISOString().split('T')[0]
    })

    const auditGroupedDocs = ref([])

    const fetchDocuments = async () => {
        isLoading.value = true
        try {
            const response = await api.get('akunting/purchase-order/')

            let realPOs = Array.isArray(response.data) ? response.data
                : (response.data?.results || response.data?.data || [response.data])

            const mappedData = realPOs.map(po => {
                const poId = po.no_po || 'UNKNOWN_PO'

                const financeStatus = statusTagihan(po) || 'Pending'
                let savedFiles = po.dokumen_audit || {
                    invoice: { exists: false, doc_no: '-', date: '-' },
                    faktur_pajak: { exists: false, doc_no: '-', date: '-' },
                    surat_jalan: { exists: false, doc_no: '-', date: '-' }
                }

                let namaPartner = po.nama_supplier || po.suplier_nama || po.supplier?.nama_suplier || '-'

                return {
                    po_id: poId,
                    partner: namaPartner,
                    date: po.tanggal || '-',
                    files: savedFiles,
                    payment_status: financeStatus
                }
            })

            auditGroupedDocs.value = mappedData
        } catch (error) {
            console.error("Gagal mengambil data PO dari server:", error)
        } finally {
            isLoading.value = false
        }
    }

    const getComplianceStats = (files) => {
        if (!files) return { count: 0, percentage: 0, isComplete: false }

        const totalRequired = 3
        let uploadedCount = 0

        if (files.invoice?.exists) uploadedCount++
        if (files.faktur_pajak?.exists) uploadedCount++
        if (files.surat_jalan?.exists) uploadedCount++

        return {
            count: uploadedCount,
            percentage: Math.round((uploadedCount / totalRequired) * 100),
            isComplete: uploadedCount === totalRequired
        }
    }

    const totalTransactions = computed(() => auditGroupedDocs.value.length)
    const fullyCompliantCount = computed(() => auditGroupedDocs.value.filter(item => getComplianceStats(item.files).isComplete).length)
    const missingDocsCount = computed(() => totalTransactions.value - fullyCompliantCount.value)

    const filteredAuditData = computed(() => {
        return auditGroupedDocs.value.filter(item => {
            const stats = getComplianceStats(item.files)
            const matchFilter = statusFilter.value === 'all' ||
                (statusFilter.value === 'lengkap' && stats.isComplete) ||
                (statusFilter.value === 'tidak_lengkap' && !stats.isComplete)

            const safePoId = String(item.po_id || '').toLowerCase()
            const safePartner = String(item.partner || '').toLowerCase()
            const safeQuery = String(searchQuery.value || '').toLowerCase()

            const matchSearch = safePoId.includes(safeQuery) || safePartner.includes(safeQuery)

            return matchFilter && matchSearch
        })
    })

    const handleUploadDocument = async () => {
        if (!uploadForm.po_reference || !uploadForm.document_number) return false

        isLoading.value = true
        try {
            // Catatan: Jika nanti saat upload error 404 juga,
            // ubah 'dokumen-audit/' menjadi 'akunting/dokumen-audit/'
            await api.post('dokumen-audit/', {
                po_reference: uploadForm.po_reference,
                document_type: uploadForm.document_type,
                document_number: uploadForm.document_number,
                upload_date: uploadForm.upload_date
            })

            await fetchDocuments()
            return true
        } catch (error) {
            console.error("Gagal upload dokumen:", error)
            alert("Gagal menyimpan dokumen ke server.")
            return false
        } finally {
            isLoading.value = false
        }
    }

    const hapusDokumen = async (item, type) => {
        if (confirm(`Hapus dokumen ${type} ini secara permanen dari server?`)) {
            isLoading.value = true
            try {
                await api.delete(`dokumen-audit/${item.po_id}/`, {
                    data: { document_type: type }
                })

                await fetchDocuments()
            } catch (error) {
                console.error("Gagal menghapus dokumen:", error)
                alert("Gagal menghapus dokumen dari server.")
            } finally {
                isLoading.value = false
            }
        }
    }

    onMounted(() => {
        fetchDocuments()
    })

    return {
        isLoading,
        searchQuery,
        statusFilter,
        uploadForm,
        auditGroupedDocs,
        totalTransactions,
        fullyCompliantCount,
        missingDocsCount,
        filteredAuditData,
        getComplianceStats,
        handleUploadDocument,
        hapusDokumen,
        fetchDocuments
    }
}