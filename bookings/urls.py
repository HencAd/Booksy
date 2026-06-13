from django.urls import path

from .views import (
    AppointmentCancelView,
    AppointmentCreateView,
    AppointmentOpinionCreate,
    AppointmentRescheduleView,
    ClientAppointmentListView,
    ProviderAppointmentCancelView,
    ProviderAppointmentListView,
    ProviderAvailabilityWeekView,
    ProviderOpinionReplyView,
    ServiceAvailabilityView,
)

urlpatterns = [
    path(
        "my-availability/",
        ProviderAvailabilityWeekView.as_view(),
        name="my_availability",
    ),
    path(
        "services/<int:pk>/availability/",
        ServiceAvailabilityView.as_view(),
        name="service_availability",
    ),
    path(
        "services/<int:pk>/book/",
        AppointmentCreateView.as_view(),
        name="appointment_create",
    ),
    path(
        "my-appointments/", ClientAppointmentListView.as_view(), name="my_appointments"
    ),
    path(
        "provider/appointments/",
        ProviderAppointmentListView.as_view(),
        name="provider_appointments",
    ),
    path(
        "my-appointments/<int:pk>/cancel/",
        AppointmentCancelView.as_view(),
        name="appointment_cancel",
    ),
    path(
        "provider/appointments/<int:pk>/cancel/",
        ProviderAppointmentCancelView.as_view(),
        name="provider_appointment_cancel",
    ),
    path(
        "appointments/<int:pk>/reschedule/",
        AppointmentRescheduleView.as_view(),
        name="appointment_reschedule",
    ),
    path(
        "appointments/<int:pk>/opinion/",
        AppointmentOpinionCreate.as_view(),
        name="appointment_opinion",
    ),
    path(
        "provider/opinions/<int:pk>/reply/",
        ProviderOpinionReplyView.as_view(),
        name="provider_opinion_reply",
    ),
]
