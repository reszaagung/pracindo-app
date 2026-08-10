from django.core.exceptions import ValidationError


class PeriodeTertutup(ValidationError):
    """Posting ke periode yang sudah dikunci."""


class NomorDokumenGagal(ValidationError):
    """Penomoran dokumen tidak bisa diselesaikan."""
