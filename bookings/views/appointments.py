from datetime import datetime, timedelta
from typing import Any, cast

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Case, IntegerField, QuerySet, Value, When
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View
from django.views.generic import ListView

from bookings.models import Appointment
from bookings.service import generate_available_slots
from services.mixins import ProviderRequiredMixin
from services.models import Service


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
            messages.error(request, "Tylko klient moĹĽe zarezerwowaÄ‡ wizytÄ™.")
            return redirect("service_availability", pk=service.pk)

        start_time_raw = request.POST.get("start_time")

        if not start_time_raw:
            messages.error(request, "Nie wybrano godziny wizyty.")
            return redirect("service_availability", pk=service.pk)

        try:
            start_time = datetime.fromisoformat(start_time_raw)
        except ValueError:
            messages.error(request, "NieprawidĹ‚owy format daty.")
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
            messages.error(request, "Ten termin nie jest juĹĽ dostÄ™pny.")
            return redirect("service_availability", pk=service.pk)

        Appointment.objects.create(
            client=request.user.client,
            provider=service.provider,
            service=service,
            start_time=start_time,
            end_time=end_time,
            status=Appointment.Status.PENDING,
        )

        messages.success(request, "Rezerwacja zostaĹ‚a utworzona.")
        return redirect("service_detail", pk=service.pk)


class ClientAppointmentListView(LoginRequiredMixin, ListView):
    model = Appointment
    template_name = "bookings/my_appointments.html"
    context_object_name = "appointments"

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if not hasattr(request.user, "client"):
            return HttpResponseForbidden(
                "Tylko klient ma dostÄ™p do swoich rezerwacji."
            )

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Appointment]:
        return (
            Appointment.objects.filter(client=self.request.user.client)
            .select_related("service", "provider", "opinion")
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
                "Tylko usĹ‚ugodawca ma dostÄ™p do swoich rezerwacji."
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
            messages.error(
                request, "Tylko klient moĹĽe zarzÄ…dzaÄ‡ swojÄ… rezerwacjÄ…."
            )
            return redirect("home")

        appointment = self.get_appointment(request, kwargs["pk"])

        if appointment.status != Appointment.Status.PENDING:
            messages.error(
                request, "MoĹĽesz zmieniÄ‡ termin tylko aktywnej rezerwacji."
            )
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
            messages.error(request, "Tylko klient moĹĽe zarezerwowaÄ‡ wizytÄ™.")
            return redirect("home")

        appointment = self.get_appointment(request, kwargs["pk"])

        if appointment.status != Appointment.Status.PENDING:
            messages.error(
                request, "MoĹĽesz zmieniÄ‡ termin tylko aktywnej rezerwacji."
            )
            return redirect("my_appointments")

        service = appointment.service
        new_start_time_raw = request.POST.get("start_time")

        if not new_start_time_raw:
            messages.error(request, "Nie wybrano godziny wizyty.")
            return redirect("appointment_reschedule", pk=appointment.pk)

        try:
            new_start_time = datetime.fromisoformat(new_start_time_raw)
        except ValueError:
            messages.error(request, "NieprawidĹ‚owy format daty.")
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
            messages.error(request, "Ten termin nie jest juĹĽ dostÄ™pny.")
            return redirect("appointment_reschedule", pk=appointment.pk)

        appointment.start_time = new_start_time
        appointment.end_time = new_end_time
        appointment.status = Appointment.Status.PENDING
        appointment.save(update_fields=["start_time", "end_time", "status"])

        messages.success(request, "Termin rezerwacji zostaĹ‚ zmieniony.")
        return redirect("my_appointments")


class AppointmentCancelView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if not hasattr(request.user, "client"):
            messages.error(request, "Tylko klient moĹĽe anulowaÄ‡ swojÄ… rezerwacjÄ™.")
            return redirect("home")

        appointment = get_object_or_404(
            Appointment,
            pk=kwargs["pk"],
            client=request.user.client,
        )

        if appointment.status != Appointment.Status.PENDING:
            messages.error(request, "MoĹĽesz anulowaÄ‡ tylko aktywnÄ… rezerwacjÄ™.")
            return redirect("my_appointments")

        appointment.status = Appointment.Status.CANCELLED
        appointment.save(update_fields=["status", "updated_at"])

        messages.success(request, "Rezerwacja zostaĹ‚a anulowana.")
        return redirect("my_appointments")


class ProviderAppointmentCancelView(LoginRequiredMixin, ProviderRequiredMixin, View):
    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if not hasattr(request.user, "provider"):
            messages.error(request, "Tylko usĹ‚ugodawca moĹĽe anulowaÄ‡ rezerwacjÄ™.")
            return redirect("home")

        appointment = get_object_or_404(
            Appointment,
            pk=kwargs["pk"],
            provider=request.user.provider,
        )

        if appointment.status != Appointment.Status.PENDING:
            messages.error(request, "MoĹĽesz anulowaÄ‡ tylko aktywnÄ… rezerwacjÄ™.")
            return redirect("my_appointments")

        appointment.status = Appointment.Status.CANCELLED
        appointment.save(update_fields=["status", "updated_at"])

        messages.success(request, "Rezerwacja zostaĹ‚a anulowana.")
        return redirect("provider_appointments")
