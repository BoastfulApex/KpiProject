from django.db import models
from django.contrib.auth.models import User


class Filial(models.Model):
    filial_name = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return self.filial_name if self.filial_name else "Unnamed Location"
    
    class Meta:
        verbose_name = "Filial"
        verbose_name_plural = "Filiallar"



class Administrator(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    telegram_id = models.BigIntegerField(unique=True)
    filial = models.ForeignKey(Filial, on_delete=models.SET_NULL, null=True, blank=True)
    full_name = models.CharField(max_length=255)

    def __str__(self):
        return self.full_name
    

class Weekday(models.Model):
    name = models.CharField(max_length=20, unique=True)
    name_en = models.CharField(max_length=20, unique=True, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Hafta kuni"
        verbose_name_plural = "Hafta kunlari"

