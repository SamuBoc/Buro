from django.db import models


class Beneficiary(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nombre")
    location = models.CharField(max_length=300, verbose_name="Ubicación")
    phone = models.CharField(max_length=20, verbose_name="Teléfono")
    email = models.EmailField(verbose_name="Correo electrónico")
    date_register = models.DateField(auto_now_add=True, verbose_name="Fecha de registro")

    class Meta:
        verbose_name = "Beneficiario"
        verbose_name_plural = "Beneficiarios"
        ordering = ['-date_register']

    def __str__(self):
        return self.name
