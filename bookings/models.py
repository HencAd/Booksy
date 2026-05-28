from django.db import models

from accounts.models import Client, Provider
from services.models import Service


class ProviderAvailability(models.Model):
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE)
    day_of_week = models.PositiveSmallIntegerField()
    start_time = models.TimeField()
    end_time = models.TimeField()


class Appointment(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.PROTECT)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(...)
    created_at = models.DateTimeField(auto_now_add=True)
