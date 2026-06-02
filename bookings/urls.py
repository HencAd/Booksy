from django.urls import path

from .views import (
    AppointmentCancelView,
    AppointmentCreateView,
    AppointmentRescheduleView,
    ClientAppointmentListView,
    ProviderAvailabilityWeekView,
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
        "my-appointments/<int:pk>/cancel/",
        AppointmentCancelView.as_view(),
        name="appointment_cancel",
    ),
    path(
        "appointments/<int:pk>/reschedule/",
        AppointmentRescheduleView.as_view(),
        name="appointment_reschedule",
    ),
]
