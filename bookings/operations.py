import logging

from django.utils import timezone

from bookings.models import Appointment

logger = logging.getLogger(__name__)


def mark_past_appointments_as_completed() -> int:
    count = Appointment.objects.filter(
        status=Appointment.Status.PENDING,
        end_time__lt=timezone.now(),
    ).update(
        status=Appointment.Status.COMPLETED,
    )

    logger.info(
        "Oznaczono %d rezerwacji jako COMPLETED.",
        count,
    )

    return count
