"""Endpoint pengguna — staff_user/views.py"""
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
# [PERBAIKAN]: Impor ValidationError dari DRF
from rest_framework.exceptions import ValidationError as DRFValidationError

from . import services
from .models import DataKepegawaian, Jabatan, Profil, RiwayatAkses
from .permissions import (
    AksesModul, DiriSendiriAtauSupervisor, HanyaAdmin, HanyaSupervisor,
    SudahLogin,
)
from .serializers import (
    AktivasiSerializer, DataKepegawaianSerializer, GantiPasswordSerializer,
    JabatanSerializer, LoginSerializer, NonaktifSerializer,
    PendaftaranSerializer, PenolakanSerializer, ProfilSerializer,
    ResetPasswordSerializer, RiwayatAksesSerializer, UbahRoleSerializer,
)


def _galat(e):
    pesan = e.message_dict if hasattr(e, 'message_dict') else {'detail': e.messages}
    return Response(pesan, status=status.HTTP_400_BAD_REQUEST)



class DaftarView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        s = PendaftaranSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        try:
            profil = services.daftar(
                username=d['username'],
                password=d['password'],
                first_name=d['nama_lengkap'],
                last_name='',
                email=d.get('email', ''),
                nomor_hp=d.get('telepon', ''),
            )
        except DjangoValidationError as e:
            return _galat(e)
        return Response(
            {
                'id': profil.id,
                'username': profil.username,
                'pesan': 'Pendaftaran diterima. Menunggu persetujuan Supervisor.',
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        s = LoginSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        username = s.validated_data['username']
        user = authenticate(
            request, username=username, password=s.validated_data['password'],
        )

        if user is None:
            ada = Profil.objects.filter(username__iexact=username).first()
            services.catat_akses(
                request=request, username=username, profil=ada,
                berhasil=False,
                alasan='password salah' if ada else 'username tidak ada',
            )
            return Response(
                {'detail': 'Username atau password salah.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.bisa_login:
            alasan = ('menunggu persetujuan' if user.menunggu_persetujuan
                      else 'akun nonaktif')
            services.catat_akses(request=request, username=username,
                                 profil=user, berhasil=False, alasan=alasan)
            return Response(
                {'detail': 'Akun belum aktif. Hubungi Supervisor.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        token = services.terbitkan_token(user)
        services.catat_akses(request=request, username=username,
                             profil=user, berhasil=True)

        return Response({
            'token': token.key,
            'profil': ProfilSerializer(user).data,
            'modul': user.modul_terbuka(),
        })


class LogoutView(APIView):
    permission_classes = [SudahLogin]

    def post(self, request):
        if request.auth:
            request.auth.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PortalView(APIView):
    """
    Daftar modul yang boleh dimasuki. Frontend memanggil ini untuk
    merender kartu dashboard, sehingga aturan akses tidak digandakan
    di kode Vue.
    """

    permission_classes = [SudahLogin]

    def get(self, request):
        u = request.user
        return Response({
            'profil': ProfilSerializer(u).data,
            'modul': u.modul_terbuka(),
            'entitas': [
                {'id': e.id, 'kode': e.kode, 'nama': e.nama}
                for e in u.entitas_terlihat()
            ],
        })


class GantiPasswordView(APIView):
    permission_classes = [SudahLogin]

    def post(self, request):
        s = GantiPasswordSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        try:
            token = services.ganti_password(profil=request.user, **s.validated_data)
        except DjangoValidationError as e:
            return _galat(e)
        return Response({'token': token.key, 'pesan': 'Password berhasil diubah.'})


class ProfilViewSet(viewsets.ModelViewSet):
    modul = 'staff_user'
    queryset = (Profil.objects
                .select_related('jabatan', 'atasan', 'entitas_default')
                .order_by('username'))
    serializer_class = ProfilSerializer
    permission_classes = [AksesModul]
    filterset_fields = ['role', 'is_active', 'status_kerja', 'jabatan']
    search_fields = ['username', 'first_name', 'last_name', 'nip']

    def get_permissions(self):
        if self.action in ('aktifkan', 'tolak', 'ubah_role', 'nonaktifkan',
                           'aktifkan_kembali', 'reset_password'):
            return [HanyaSupervisor()]
        if self.action in ('create', 'destroy'):
            return [HanyaAdmin()]
        return super().get_permissions()

    def perform_destroy(self, instance):
        raise DRFValidationError(
            'Akun tidak boleh dihapus. Gunakan aksi nonaktifkan.'
        )

    @action(detail=False, methods=['get'], permission_classes=[SudahLogin])
    def saya(self, request):
        return Response(ProfilSerializer(request.user).data)

    @action(detail=False, methods=['get'], permission_classes=[HanyaSupervisor])
    def menunggu(self, request):
        qs = Profil.objects.menunggu_persetujuan()
        return Response(ProfilSerializer(qs, many=True).data)

    @action(detail=True, methods=['post'])
    def aktifkan(self, request, pk=None):
        s = AktivasiSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        try:
            profil = services.aktifkan(
                profil_id=pk, oleh=request.user, role=d['role'],
                jabatan_id=d.get('jabatan'), nip=d.get('nip') or None,
                entitas_default_id=d.get('entitas_default'),
                entitas_diizinkan_ids=d.get('entitas_diizinkan'),
                atasan_id=d.get('atasan'),
                tanggal_masuk=d.get('tanggal_masuk'),
            )
        except DjangoValidationError as e:
            return _galat(e)
        return Response(ProfilSerializer(profil).data)

    @action(detail=True, methods=['post'])
    def tolak(self, request, pk=None):
        s = PenolakanSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        try:
            profil = services.tolak(profil_id=pk, oleh=request.user,
                                    alasan=s.validated_data['alasan'])
        except DjangoValidationError as e:
            return _galat(e)
        return Response(ProfilSerializer(profil).data)

    @action(detail=True, methods=['post'], url_path='ubah-role')
    def ubah_role(self, request, pk=None):
        s = UbahRoleSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        try:
            profil = services.ubah_role(
                profil_id=pk, role_baru=s.validated_data['role'],
                oleh=request.user, alasan=s.validated_data.get('alasan', ''),
            )
        except DjangoValidationError as e:
            return _galat(e)
        return Response(ProfilSerializer(profil).data)

    @action(detail=True, methods=['post'])
    def nonaktifkan(self, request, pk=None):
        s = NonaktifSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        try:
            profil = services.nonaktifkan(
                profil_id=pk, oleh=request.user,
                tanggal_keluar=s.validated_data.get('tanggal_keluar'),
                alasan=s.validated_data.get('alasan', ''),
            )
        except DjangoValidationError as e:
            return _galat(e)
        return Response(ProfilSerializer(profil).data)

    @action(detail=True, methods=['post'], url_path='aktifkan-kembali')
    def aktifkan_kembali(self, request, pk=None):
        try:
            profil = services.aktifkan_kembali(profil_id=pk, oleh=request.user)
        except DjangoValidationError as e:
            return _galat(e)
        return Response(ProfilSerializer(profil).data)

    @action(detail=True, methods=['post'], url_path='reset-password')
    def reset_password(self, request, pk=None):
        s = ResetPasswordSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        try:
            services.reset_password(
                profil_id=pk, password_baru=s.validated_data['password_baru'],
                oleh=request.user,
            )
        except DjangoValidationError as e:
            return _galat(e)
        return Response({'pesan': 'Password direset. Sesi lama dimatikan.'})


class JabatanViewSet(viewsets.ModelViewSet):
    modul = 'staff_user'
    queryset = Jabatan.objects.all()
    serializer_class = JabatanSerializer
    permission_classes = [AksesModul]
    filterset_fields = ['departemen', 'aktif']
    search_fields = ['kode', 'nama']


class DataKepegawaianViewSet(viewsets.ModelViewSet):
    modul = 'staff_user'
    serializer_class = DataKepegawaianSerializer
    permission_classes = [SudahLogin, DiriSendiriAtauSupervisor]

    def get_queryset(self):
        qs = DataKepegawaian.objects.select_related('profil')
        if self.request.user.supervisor:
            return qs
        return qs.filter(profil=self.request.user)


class RiwayatAksesViewSet(viewsets.ReadOnlyModelViewSet):
    modul = 'staff_user'
    queryset = RiwayatAkses.objects.select_related('profil')
    serializer_class = RiwayatAksesSerializer
    permission_classes = [HanyaSupervisor]
    filterset_fields = ['berhasil', 'profil']
    search_fields = ['username_dicoba', 'ip']