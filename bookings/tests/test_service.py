from datetime import datetime, time, timedelta

from django.test import TestCase
from django.utils import timezone

from accounts.tests.factories import ProviderFactory
from bookings.models import Appointment, ProviderAvailability, ProviderBookingSettings
from bookings.service import generate_available_slots
from bookings.tests.factories import create_appointment, create_service


class GenerateAvailableSlotsTests(TestCase):
    def create_availability(self, provider, date, start=time(9, 0), end=time(11, 0)):
        return ProviderAvailability.objects.create(
            provider=provider,
            day_of_week=date.weekday(),
            start_time=start,
            end_time=end,
        )

    def get_day(self, days, date):
        return next(day for day in days if day["date"] == date)

    def test_creates_default_booking_settings_when_missing(self):
        service = create_service()

        generate_available_slots(service)

        settings = ProviderBookingSettings.objects.get(provider=service.provider)
        self.assertEqual(
            settings.slot_interval_minutes,
            ProviderBookingSettings.SlotInterval.THIRTY,
        )

    def test_generates_slots_for_provider_availability(self):
        date = timezone.localdate() + timedelta(days=1)
        provider = ProviderFactory()
        service = create_service(provider=provider, duration_minutes=60)
        ProviderBookingSettings.objects.create(
            provider=provider,
            slot_interval_minutes=ProviderBookingSettings.SlotInterval.THIRTY,
        )
        self.create_availability(provider, date)

        days = generate_available_slots(service)
        slots = self.get_day(days, date)["slots"]

        self.assertEqual(len(slots), 3)
        self.assertEqual(slots[0]["start"].time(), time(9, 0))
        self.assertEqual(slots[1]["start"].time(), time(9, 30))
        self.assertEqual(slots[2]["start"].time(), time(10, 0))

    def test_does_not_return_slots_without_availability(self):
        service = create_service()

        days = generate_available_slots(service)

        self.assertTrue(all(day["slots"] == [] for day in days))

    def test_excludes_slots_that_collide_with_active_appointments(self):
        date = timezone.localdate() + timedelta(days=1)
        provider = ProviderFactory()
        service = create_service(provider=provider, duration_minutes=60)
        ProviderBookingSettings.objects.create(
            provider=provider,
            slot_interval_minutes=ProviderBookingSettings.SlotInterval.THIRTY,
        )
        self.create_availability(provider, date)
        start_time = timezone.make_aware(datetime.combine(date, time(9, 30)))
        create_appointment(
            provider=provider,
            service=service,
            start_time=start_time,
            end_time=start_time + timedelta(minutes=60),
            status=Appointment.Status.PENDING,
        )

        days = generate_available_slots(service)
        slots = self.get_day(days, date)["slots"]

        self.assertEqual(len(slots), 0)

    def test_cancelled_appointments_do_not_block_slots(self):
        date = timezone.localdate() + timedelta(days=1)
        provider = ProviderFactory()
        service = create_service(provider=provider, duration_minutes=60)
        ProviderBookingSettings.objects.create(
            provider=provider,
            slot_interval_minutes=ProviderBookingSettings.SlotInterval.THIRTY,
        )
        self.create_availability(provider, date)
        start_time = timezone.make_aware(datetime.combine(date, time(9, 30)))
        create_appointment(
            provider=provider,
            service=service,
            start_time=start_time,
            end_time=start_time + timedelta(minutes=60),
            status=Appointment.Status.CANCELLED,
        )

        days = generate_available_slots(service)
        slots = self.get_day(days, date)["slots"]

        self.assertEqual(len(slots), 3)

    def test_exclude_appointment_keeps_its_current_slot_available(self):
        date = timezone.localdate() + timedelta(days=1)
        provider = ProviderFactory()
        service = create_service(provider=provider, duration_minutes=60)
        ProviderBookingSettings.objects.create(
            provider=provider,
            slot_interval_minutes=ProviderBookingSettings.SlotInterval.THIRTY,
        )
        self.create_availability(provider, date)
        start_time = timezone.make_aware(datetime.combine(date, time(9, 30)))
        appointment = create_appointment(
            provider=provider,
            service=service,
            start_time=start_time,
            end_time=start_time + timedelta(minutes=60),
            status=Appointment.Status.PENDING,
        )

        days = generate_available_slots(service, exclude_appointment=appointment)
        slots = self.get_day(days, date)["slots"]

        self.assertEqual(len(slots), 3)
