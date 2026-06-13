from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from accounts.models import Client, Provider
from services.models import Service


class ProviderAvailability(models.Model):
    class DayOfWeek(models.IntegerChoices):
        MONDAY = 0, "Poniedziałek"
        TUESDAY = 1, "Wtorek"
        WEDNESDAY = 2, "Środa"
        THURSDAY = 3, "Czwartek"
        FRIDAY = 4, "Piątek"
        SATURDAY = 5, "Sobota"
        SUNDAY = 6, "Niedziela"

    provider = models.ForeignKey(Provider, on_delete=models.CASCADE)
    day_of_week = models.PositiveSmallIntegerField(choices=DayOfWeek.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "day_of_week"],
                name="unique_provider_day_availability",
            )
        ]

    def __str__(self) -> str:
        return f"{self.provider} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"


class Appointment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Oczekująca"
        CANCELLED = "cancelled", "Anulowana"
        COMPLETED = "completed", "Zakończona"

    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.PROTECT)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class AppointmentOpinion(models.Model):
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name="opinion",
    )
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    opinion = models.TextField(blank=True)
    provider_response = models.TextField(blank=True)
    stars = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5),
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ProviderBookingSettings(models.Model):
    class SlotInterval(models.IntegerChoices):
        FIFTEEN = 15, "15 minut"
        THIRTY = 30, "30 minut"
        SIXTY = 60, "1 godzina"

    provider = models.OneToOneField(Provider, on_delete=models.CASCADE)
    slot_interval_minutes = models.PositiveSmallIntegerField(
        choices=SlotInterval.choices, default=SlotInterval.THIRTY
    )

    def __str__(self) -> str:
        return f"{self.provider} - slot co {self.slot_interval_minutes} min"
