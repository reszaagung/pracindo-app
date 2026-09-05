from django.db import models
from django.conf import settings

class HelperGenerateStikerDoc(models.Model):
    kode = models.CharField(max_length=100, null=True, blank=True)
    nama_item = models.CharField(max_length=100, null=True, blank=True)
    tipe = models.CharField(max_length=100, null=True, blank=True)
    lot = models.CharField(max_length=100, null=True, blank=True)
    total_unit = models.IntegerField(default=1, verbose_name="Total Unit") 
    qty = models.CharField(max_length=100, null=True, blank=True) 

    class Meta:
        db_table = "helper_generate_stiker_doc"
        verbose_name = "Helper Generate Stiker Doc"
        verbose_name_plural = "Helper Generate Stiker Docs"

    def __str__(self):
        return f"{self.kode} - {self.nama_item}"