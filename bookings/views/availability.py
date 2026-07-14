from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views import View

from bookings.models import ProviderAvailability, ProviderBookingSettings
from services.mixins import ProviderRequiredMixin


class ProviderAvailabilityWeekView(LoginRequiredMixin, ProviderRequiredMixin, View):
    template_name = "bookings/my_availability_week.html"

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        provider = request.user.provider

        booking_settings, created = ProviderBookingSettings.objects.get_or_create(
            provider=provider
        )

        existing_availabilities = ProviderAvailability.objects.filter(provider=provider)

        availability_by_day = {
            availability.day_of_week: availability
            for availability in existing_availabilities
        }

        days = []

        for day_value, day_label in ProviderAvailability.DayOfWeek.choices:
            availability = availability_by_day.get(day_value)

            days.append(
                {
                    "value": day_value,
                    "label": day_label,
                    "is_enabled": availability is not None,
                    "start_time": availability.start_time.strftime("%H:%M")
                    if availability
                    else "",
                    "end_time": availability.end_time.strftime("%H:%M")
                    if availability
                    else "",
                }
            )

        return render(
            request,
            self.template_name,
            {
                "days": days,
                "booking_settings": booking_settings,
                "slot_interval_choices": ProviderBookingSettings.SlotInterval.choices,
            },
        )

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        provider = request.user.provider
        cleaned_days = []

        slot_interval_minutes = request.POST.get("slot_interval_minutes")

        allowed_intervals = [
            str(choice[0]) for choice in ProviderBookingSettings.SlotInterval.choices
        ]

        if slot_interval_minutes not in allowed_intervals:
            messages.error(request, "Niepoprawny interwaĹ‚ slotĂłw.")
            return redirect("my_availability")

        for day_value, day_label in ProviderAvailability.DayOfWeek.choices:
            is_enabled = request.POST.get(f"day_{day_value}_enabled")
            start_time = request.POST.get(f"day_{day_value}_start")
            end_time = request.POST.get(f"day_{day_value}_end")

            if is_enabled:
                if not start_time or not end_time:
                    messages.error(
                        request, f"UzupeĹ‚nij godziny pracy dla dnia: {day_label}."
                    )
                    return redirect("my_availability")

                if start_time >= end_time:
                    messages.error(
                        request,
                        f"Godzina rozpoczÄ™cia musi byÄ‡ wczeĹ›niejsza niĹĽ zakoĹ„czenia: {day_label}.",
                    )
                    return redirect("my_availability")

            cleaned_days.append(
                {
                    "day_value": day_value,
                    "is_enabled": is_enabled,
                    "start_time": start_time,
                    "end_time": end_time,
                }
            )

        with transaction.atomic():
            booking_settings, created = ProviderBookingSettings.objects.get_or_create(
                provider=provider
            )
            booking_settings.slot_interval_minutes = slot_interval_minutes
            booking_settings.save(update_fields=["slot_interval_minutes"])

            for day in cleaned_days:
                existing_availability = ProviderAvailability.objects.filter(
                    provider=provider, day_of_week=day["day_value"]
                ).first()

                if day["is_enabled"]:
                    if existing_availability:
                        existing_availability.start_time = day["start_time"]
                        existing_availability.end_time = day["end_time"]
                        existing_availability.save(
                            update_fields=["start_time", "end_time"]
                        )
                    else:
                        ProviderAvailability.objects.create(
                            provider=provider,
                            day_of_week=day["day_value"],
                            start_time=day["start_time"],
                            end_time=day["end_time"],
                        )
                else:
                    if existing_availability:
                        existing_availability.delete()

        messages.success(request, "DostÄ™pnoĹ›Ä‡ zostaĹ‚a zaktualizowana.")
        return redirect("my_availability")
