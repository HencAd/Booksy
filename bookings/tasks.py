from celery import shared_task

from bookings.operations import mark_past_appointments_as_completed as mark_completed


@shared_task
def mark_past_appointments_as_completed() -> int:
    return mark_completed()
