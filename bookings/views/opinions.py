from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View

from bookings.models import Appointment, AppointmentOpinion
from services.mixins import ProviderRequiredMixin


class AppointmentOpinionCreate(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if not hasattr(request.user, "client"):
            messages.error(request, "Tylko klient moĹĽe oceniÄ‡ wizytÄ™.")
            return redirect("home")

        appointment = get_object_or_404(
            Appointment,
            pk=kwargs["pk"],
            client=request.user.client,
        )

        if appointment.status != Appointment.Status.COMPLETED:
            messages.error(request, "MoĹĽesz oceniÄ‡ tylko zrealizowanÄ… usĹ‚ugÄ™.")
            return redirect("my_appointments")

        if hasattr(appointment, "opinion"):
            messages.error(request, "Ta wizyta zostaĹ‚a juĹĽ oceniona.")
            return redirect("my_appointments")

        opinion = request.POST.get("opinion")
        stars_raw = request.POST.get("stars")

        if not stars_raw:
            messages.error(request, "UzupeĹ‚nij ocenÄ™")
            return redirect("my_appointments")

        try:
            stars = int(stars_raw)
        except ValueError:
            messages.error(request, "NieprawidĹ‚owa ocena.")
            return redirect("my_appointments")

        if stars < 1 or stars > 5:
            messages.error(request, "Ocena musi byÄ‡ w zakresie od 1 do 5.")
            return redirect("my_appointments")

        AppointmentOpinion.objects.create(
            appointment=appointment,
            client=request.user.client,
            opinion=opinion,
            stars=stars,
        )

        messages.success(request, "DziÄ™kujemy za wystawienie opinii.")
        return redirect("my_appointments")


class ProviderOpinionReplyView(LoginRequiredMixin, ProviderRequiredMixin, View):
    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        opinion = get_object_or_404(
            AppointmentOpinion,
            pk=kwargs["pk"],
            appointment__provider=request.user.provider,
        )

        if opinion.provider_response:
            messages.error(request, "OdpowiedĹş zostaĹ‚a juĹĽ dodana.")
            return redirect("my_service_detail", pk=opinion.appointment.service.pk)

        response = request.POST.get("provider_response", "").strip()

        if not response:
            messages.error(request, "TreĹ›Ä‡ odpowiedzi nie moĹĽe byÄ‡ pusta.")
            return redirect("my_service_detail", pk=opinion.appointment.service.pk)

        opinion.provider_response = response
        opinion.save(update_fields=["provider_response", "updated_at"])

        messages.success(request, "OdpowiedĹş zostaĹ‚a dodana.")
        return redirect("my_service_detail", pk=opinion.appointment.service.pk)
