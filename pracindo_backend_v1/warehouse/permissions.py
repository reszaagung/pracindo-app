# warehouse/permissions.py
class OperatorGudang(BasePermission):
    """
    Menyahkan penerimaan berarti menciptakan hak atas rupiah. Itu bukan
    tugas siapa pun yang kebetulan punya akses modul warehouse.
    """
    def has_permission(self, request, view):
        return (AksesWarehouse().has_permission(request, view)
                and request.user.has_perm("warehouse.post_penerimaan"))