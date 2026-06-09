from datetime import datetime, timedelta
from typing import Any, cast

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Case, IntegerField, QuerySet, Value, When
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View
from django.views.generic import ListView

from services.mixins import ProviderRequiredMixin
from services.models import Service

from .models import Appointment, ProviderAvailability, ProviderBookingSettings
from .service import generate_available_slots


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
            messages.error(request, "Niepoprawny interwał slotów.")
            return redirect("my_availability")

        for day_value, day_label in ProviderAvailability.DayOfWeek.choices:
            is_enabled = request.POST.get(f"day_{day_value}_enabled")
            start_time = request.POST.get(f"day_{day_value}_start")
            end_time = request.POST.get(f"day_{day_value}_end")

            if is_enabled:
                if not start_time or not end_time:
                    messages.error(
                        request, f"Uzupełnij godziny pracy dla dnia: {day_label}."
                    )
                    return redirect("my_availability")

                if start_time >= end_time:
                    messages.error(
                        request,
                        f"Godzina rozpoczęcia musi być wcześniejsza niż zakończenia: {day_label}.",
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

        messages.success(request, "Dostępność została zaktualizowana.")
        return redirect("my_availability")


class ServiceAvailabilityView(View):
    template_name = "bookings/service_availability.html"

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        service = get_object_or_404(
            Service.objects.select_related("provider"), pk=kwargs["pk"], is_active=True
        )

        week = request.GET.get("week", 0)
        try:
            week = int(week)
        except ValueError:
            week = 0

        if week < 0:
            week = 0

        # na razie ograniczenie do kolejnego tygodnia
        if week > 1:
            week = 1

        days = generate_available_slots(service, week=week)

        return render(
            request,
            self.template_name,
            {
                "service": service,
                "days": days,
                "week": week,
                "previous_week": week - 1,
                "next_week": week + 1,
            },
        )


class AppointmentCreateView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        service = get_object_or_404(
            Service.objects.select_related("provider"),
            pk=kwargs["pk"],
            is_active=True,
        )

        if not hasattr(request.user, "client"):
            messages.error(request, "Tylko klient może zarezerwować wizytę.")
            return redirect("service_availability", pk=service.pk)

        start_time_raw = request.POST.get("start_time")

        if not start_time_raw:
            messages.error(request, "Nie wybrano godziny wizyty.")
            return redirect("service_availability", pk=service.pk)

        try:
            start_time = datetime.fromisoformat(start_time_raw)
        except ValueError:
            messages.error(request, "Nieprawidłowy format daty.")
            return redirect("service_availability", pk=service.pk)

        if timezone.is_naive(start_time):
            start_time = timezone.make_aware(start_time)

        end_time = start_time + timedelta(minutes=service.duration_minutes)

        has_collision = Appointment.objects.filter(
            provider=service.provider,
            status__in=[
                Appointment.Status.PENDING,
                Appointment.Status.COMPLETED,
            ],
            start_time__lt=end_time,
            end_time__gt=start_time,
        ).exists()

        if has_collision:
            messages.error(request, "Ten termin nie jest już dostępny.")
            return redirect("service_availability", pk=service.pk)

        Appointment.objects.create(
            client=request.user.client,
            provider=service.provider,
            service=service,
            start_time=start_time,
            end_time=end_time,
            status=Appointment.Status.PENDING,
        )

        messages.success(request, "Rezerwacja została utworzona.")
        return redirect("service_detail", pk=service.pk)


class ClientAppointmentListView(LoginRequiredMixin, ListView):
    model = Appointment
    template_name = "bookings/my_appointments.html"
    context_object_name = "appointments"

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if not hasattr(request.user, "client"):
            return HttpResponseForbidden("Tylko klient ma dostęp do swoich rezerwacji.")

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Appointment]:
        return (
            Appointment.objects.filter(client=self.request.user.client)
            .select_related("service", "provider")
            .annotate(
                status_order=Case(
                    When(status=Appointment.Status.PENDING, then=Value(1)),
                    When(status=Appointment.Status.CANCELLED, then=Value(2)),
                    When(status=Appointment.Status.COMPLETED, then=Value(3)),
                    default=Value(4),
                    output_field=IntegerField(),
                )
            )
            .order_by("status_order", "start_time")
        )


class ProviderAppointmentListView(LoginRequiredMixin, ListView):
    model = Appointment
    template_name = "bookings/provider_appointments.html"
    context_object_name = "appointments"

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if not hasattr(request.user, "provider"):
            return HttpResponseForbidden(
                "Tylko usługodawca ma dostęp do swoich rezerwacji."
            )

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Appointment]:
        return (
            Appointment.objects.filter(provider=self.request.user.provider)
            .select_related("service", "client", "client__user")
            .annotate(
                status_order=Case(
                    When(status=Appointment.Status.PENDING, then=Value(1)),
                    When(status=Appointment.Status.CANCELLED, then=Value(2)),
                    When(status=Appointment.Status.COMPLETED, then=Value(3)),
                    default=Value(4),
                    output_field=IntegerField(),
                )
            )
            .order_by("status_order", "start_time")
        )


class AppointmentRescheduleView(LoginRequiredMixin, View):
    template_name = "bookings/reschedule_appointments.html"

    def get_appointment(self, request: HttpRequest, pk: int) -> Appointment:

        appointment = get_object_or_404(
            Appointment.objects.select_related("service", "provider", "client"),
            pk=pk,
            client=request.user.client,
        )

        return cast(Appointment, appointment)

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:

        if not hasattr(request.user, "client"):
            messages.error(request, "Tylko klient może zarządzać swoją rezerwacją.")
            return redirect("home")

        appointment = self.get_appointment(request, kwargs["pk"])

        if appointment.status != Appointment.Status.PENDING:
            messages.error(request, "Możesz zmienić termin tylko aktywnej rezerwacji.")
            return redirect("my_appointments")

        service = appointment.service

        week = int(request.GET.get("week", 0))

        if week < 0:
            week = 0

        if week > 1:
            week = 1

        days = generate_available_slots(
            service,
            week=week,
            exclude_appointment=appointment,
        )

        return render(
            request,
            self.template_name,
            {
                "appointment": appointment,
                "service": service,
                "days": days,
                "week": week,
                "previous_week": week - 1,
                "next_week": week + 1,
            },
        )

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:

        if not hasattr(request.user, "client"):
            messages.error(request, "Tylko klient może zarezerwować wizytę.")
            return redirect("home")

        appointment = self.get_appointment(request, kwargs["pk"])

        if appointment.status != Appointment.Status.PENDING:
            messages.error(request, "Możesz zmienić termin tylko aktywnej rezerwacji.")
            return redirect("my_appointments")

        service = appointment.service
        new_start_time_raw = request.POST.get("start_time")

        if not new_start_time_raw:
            messages.error(request, "Nie wybrano godziny wizyty.")
            return redirect("appointment_reschedule", pk=appointment.pk)

        try:
            new_start_time = datetime.fromisoformat(new_start_time_raw)
        except ValueError:
            messages.error(request, "Nieprawidłowy format daty.")
            return redirect("appointment_reschedule", pk=appointment.pk)

        if timezone.is_naive(new_start_time):
            new_start_time = timezone.make_aware(new_start_time)

        new_end_time = new_start_time + timedelta(minutes=service.duration_minutes)

        has_collision = (
            Appointment.objects.filter(
                provider=appointment.provider,
                status__in=[
                    Appointment.Status.PENDING,
                ],
                start_time__lt=new_end_time,
                end_time__gt=new_start_time,
            )
            .exclude(pk=appointment.pk)
            .exists()
        )

        if has_collision:
            messages.error(request, "Ten termin nie jest już dostępny.")
            return redirect("appointment_reschedule", pk=appointment.pk)

        appointment.start_time = new_start_time
        appointment.end_time = new_end_time
        appointment.status = Appointment.Status.PENDING
        appointment.save(update_fields=["start_time", "end_time", "status"])

        messages.success(request, "Termin rezerwacji został zmieniony.")
        return redirect("my_appointments")


class AppointmentCancelView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if not hasattr(request.user, "client"):
            messages.error(request, "Tylko klient może anulować swoją rezerwację.")
            return redirect("home")

        appointment = get_object_or_404(
            Appointment,
            pk=kwargs["pk"],
            client=request.user.client,
        )

        if appointment.status != Appointment.Status.PENDING:
            messages.error(request, "Możesz anulować tylko aktywną rezerwację.")
            return redirect("my_appointments")

        appointment.status = Appointment.Status.CANCELLED
        appointment.save(update_fields=["status", "updated_at"])

        messages.success(request, "Rezerwacja została anulowana.")
        return redirect("my_appointments")


class ProviderAppointmentCancelView(LoginRequiredMixin, ProviderRequiredMixin, View):
    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if not hasattr(request.user, "provider"):
            messages.error(request, "Tylko usługodawca może anulować rezerwację.")
            return redirect("home")

        appointment = get_object_or_404(
            Appointment,
            pk=kwargs["pk"],
            provider=request.user.provider,
        )

        if appointment.status != Appointment.Status.PENDING:
            messages.error(request, "Możesz anulować tylko aktywną rezerwację.")
            return redirect("my_appointments")

        appointment.status = Appointment.Status.CANCELLED
        appointment.save(update_fields=["status", "updated_at"])

        messages.success(request, "Rezerwacja została anulowana.")
        return redirect("provider_appointments")
