from datetime import datetime, timedelta

from django.utils import timezone

from .models import Appointment, ProviderAvailability, ProviderBookingSettings


def generate_available_slots(service, week=0):
    provider = service.provider

    booking_settings, created = ProviderBookingSettings.objects.get_or_create(
        provider=provider
    )

    slot_interval = timedelta(minutes=booking_settings.slot_interval_minutes)
    service_duration = timedelta(minutes=service.duration_minutes)

    today = timezone.localdate()
    start_date = today + timedelta(days=week * 7)

    availabilities = ProviderAvailability.objects.filter(provider=provider)
    availability_by_day = {
        availability.day_of_week: availability for availability in availabilities
    }

    days = []

    for i in range(7):
        day_date = start_date + timedelta(days=i)
        day_of_week = day_date.weekday()  # Monday = 0, Sunday = 6

        availability = availability_by_day.get(day_of_week)

        day_data = {
            "date": day_date,
            "label": day_date.strftime("%A"),
            "slots": [],
        }

        if not availability:
            days.append(day_data)
            continue

        work_start = timezone.make_aware(
            datetime.combine(day_date, availability.start_time)
        )
        work_end = timezone.make_aware(
            datetime.combine(day_date, availability.end_time)
        )

        active_appointments = Appointment.objects.filter(
            provider=provider,
            start_time__date=day_date,
            status__in=[
                Appointment.Status.PENDING,
                Appointment.Status.COMPLETED,
            ],
        )

        current_start = work_start
        now = timezone.now()

        while current_start + service_duration <= work_end:
            current_end = current_start + service_duration

            if current_start < now:
                current_start += slot_interval
                continue

            has_collision = active_appointments.filter(
                start_time__lt=current_end,
                end_time__gt=current_start,
            ).exists()

            if not has_collision:
                day_data["slots"].append(
                    {
                        "start": current_start,
                        "end": current_end,
                    }
                )

            current_start += slot_interval

        days.append(day_data)

    return days
