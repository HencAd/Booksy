from typing import Any, cast

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q, QuerySet
from django.forms import ModelForm
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from bookings.models import AppointmentOpinion

from .mixins import ProviderRequiredMixin
from .models import Service


class ServiceListView(ListView):
    model = Service
    template_name = "services/service_list.html"
    context_object_name = "services"

    def get_queryset(self) -> QuerySet[Service]:
        queryset = (
            Service.objects.filter(is_active=True)
            .select_related("provider")
            .order_by("-created_at")
        )

        q = self.request.GET.get("q")
        min_price = self.request.GET.get("min_price")
        max_price = self.request.GET.get("max_price")

        if q:
            queryset = queryset.filter(
                Q(name__icontains=q)
                | Q(description__icontains=q)
                | Q(provider__business_name__icontains=q)
            )

        if min_price:
            queryset = queryset.filter(price__gte=min_price)

        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        return queryset


class ServiceDetailView(DetailView):
    model = Service
    template_name = "services/service_detail.html"
    context_object_name = "service"

    def get_queryset(self) -> QuerySet[Service]:
        return Service.objects.filter(is_active=True).select_related("provider")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = cast(dict[str, Any], super().get_context_data(**kwargs))

        context["opinions"] = (
            AppointmentOpinion.objects.filter(appointment__service=self.object)
            .select_related("client", "client__user", "appointment")
            .order_by("-created_at")
        )

        return context


class ProviderServiceListView(LoginRequiredMixin, ProviderRequiredMixin, ListView):
    model = Service
    template_name = "services/my_service_list.html"
    context_object_name = "services"

    def get_queryset(self) -> QuerySet[Service]:
        return Service.objects.filter(provider=self.request.user.provider).order_by(
            "-created_at"
        )


class ProviderServiceDetailView(LoginRequiredMixin, ProviderRequiredMixin, DetailView):
    model = Service
    template_name = "services/my_service_detail.html"
    context_object_name = "service"

    def get_queryset(self) -> QuerySet[Service]:
        return Service.objects.filter(provider=self.request.user.provider)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = cast(dict[str, Any], super().get_context_data(**kwargs))

        context["opinions"] = (
            AppointmentOpinion.objects.filter(appointment__service=self.object)
            .select_related("client", "client__user", "appointment")
            .order_by("-created_at")
        )

        return context


class ServiceCreateView(
    LoginRequiredMixin, ProviderRequiredMixin, SuccessMessageMixin, CreateView
):
    model = Service
    template_name = "services/service_form.html"
    fields = ["name", "description", "price", "duration_minutes", "is_active"]
    success_message = "Usługa została dodana."
    success_url = reverse_lazy("my_service_list")

    def form_valid(self, form: ModelForm) -> HttpResponse:
        form.instance.provider = self.request.user.provider
        return super().form_valid(form)


class ServiceUpdateView(
    LoginRequiredMixin, ProviderRequiredMixin, SuccessMessageMixin, UpdateView
):
    model = Service
    template_name = "services/service_form.html"
    fields = ["name", "description", "price", "duration_minutes", "is_active"]
    success_message = "Usługa została zaktualizowana."
    success_url = reverse_lazy("my_service_list")

    def get_queryset(self) -> QuerySet[Service]:
        return Service.objects.filter(provider=self.request.user.provider)


class ServiceDeactivateView(LoginRequiredMixin, ProviderRequiredMixin, View):
    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        service = get_object_or_404(
            Service, pk=kwargs["pk"], provider=request.user.provider
        )

        service.is_active = False
        service.save(update_fields=["is_active", "updated_at"])

        messages.success(request, "Usługa została dezaktywowana.")
        return redirect("my_service_list")
