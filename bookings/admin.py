from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from .models import Appointment, ProviderAvailability, ProviderBookingSettings


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = [
        "service",
        "client",
        "provider",
        "start_time",
        "end_time",
        "status",
    ]
    list_filter = ["status", "provider", "service", "start_time"]
    search_fields = [
        "service__name",
        "provider__business_name",
        "client__user__username",
        "client__user__email",
    ]
    ordering = ["start_time"]
    actions = ["cancel_appointments"]

    @admin.action(description="Anuluj wybrane rezerwacje")
    def cancel_appointments(self, request: HttpRequest, queryset: QuerySet) -> None:
        queryset.update(status=Appointment.Status.CANCELLED)


@admin.register(ProviderAvailability)
class ProviderAvailabilityAdmin(admin.ModelAdmin):
    list_display = ["provider", "day_of_week", "start_time", "end_time"]
    list_filter = ["provider", "day_of_week"]


@admin.register(ProviderBookingSettings)
class ProviderBookingSettingsAdmin(admin.ModelAdmin):
    list_display = ["provider", "slot_interval_minutes"]
