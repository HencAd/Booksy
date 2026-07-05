import logging

from celery import shared_task
from django.utils import timezone

from .models import Appointment

logger = logging.getLogger(__name__)


@shared_task
def mark_past_appointments_as_completed() -> int:
    count = Appointment.objects.filter(
        status=Appointment.Status.PENDING,
        end_time__lt=timezone.now(),
    ).update(
        status=Appointment.Status.COMPLETED,
    )

    logger.info("Oznaczono %d rezerwacji jako COMPLETED.", count)

    return count
