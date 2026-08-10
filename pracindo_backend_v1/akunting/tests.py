from django.test import SimpleTestCase

from .views import _idem


class IdemKeyTest(SimpleTestCase):
    """
    Penjaga regresi. Kunci ini pernah diacak dengan uuid4() di server,
    yang membuat setiap retry lolos sebagai pembayaran kedua.
    """

    class _Req:
        def __init__(self, headers):
            self.headers = headers

    def test_header_sama_menghasilkan_kunci_sama(self):
        r = self._Req({'Idempotency-Key': 'abc-123'})
        self.assertEqual(_idem(r, 'bayar'), 'bayar:abc-123')
        self.assertEqual(_idem(r, 'bayar'), _idem(r, 'bayar'))

    def test_tanpa_header_tetap_unik_per_request(self):
        r = self._Req({})
        self.assertNotEqual(_idem(r, 'bayar'), _idem(r, 'bayar'))
