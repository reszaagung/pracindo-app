from django.db import models

class CabangToko(models.Model):
    kode = models.CharField(max_length=20, unique=True)
    nama = models.CharField(max_length=100)
    alamat = models.TextField(blank=True, null=True)
    aktif = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.kode} - {self.nama}"