from datetime import time

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models.deletion import ProtectedError
from django.test import TestCase

from accounts.tests.factories import ProviderFactory
from bookings.models import (
    Appointment,
    AppointmentOpinion,
    ProviderAvailability,
    ProviderBookingSettings,
)
from bookings.tests.factories import create_appointment


class ProviderAvailabilityModelTests(TestCase):
    def test_str_contains_provider_day_and_working_hours(self):
        availability = ProviderAvailability.objects.create(
            provider=ProviderFactory(),
            day_of_week=ProviderAvailability.DayOfWeek.MONDAY,
            start_time=time(9, 0),
            end_time=time(17, 0),
        )

        value = str(availability)

        self.assertIn("Poniedzia", value)
        self.assertIn("09:00:00-17:00:00", value)

    def test_provider_can_have_only_one_availability_per_day(self):
        provider = ProviderFactory()
        ProviderAvailability.objects.create(
            provider=provider,
            day_of_week=ProviderAvailability.DayOfWeek.MONDAY,
            start_time=time(9, 0),
            end_time=time(17, 0),
        )

        with self.assertRaises(IntegrityError):
            ProviderAvailability.objects.create(
                provider=provider,
                day_of_week=ProviderAvailability.DayOfWeek.MONDAY,
                start_time=time(10, 0),
                end_time=time(18, 0),
            )

    def test_availability_is_deleted_when_provider_is_deleted(self):
        availability = ProviderAvailability.objects.create(
            provider=ProviderFactory(),
            day_of_week=ProviderAvailability.DayOfWeek.TUESDAY,
            start_time=time(9, 0),
            end_time=time(17, 0),
        )

        availability.provider.delete()

        self.assertFalse(
            ProviderAvailability.objects.filter(pk=availability.pk).exists()
        )


class AppointmentModelTests(TestCase):
    def test_create_appointment_with_pending_status_by_default(self):
        appointment = create_appointment()

        self.assertEqual(appointment.status, Appointment.Status.PENDING)
        self.assertIsNotNone(appointment.created_at)
        self.assertIsNotNone(appointment.updated_at)

    def test_appointment_is_deleted_when_client_is_deleted(self):
        appointment = create_appointment()

        appointment.client.delete()

        self.assertFalse(Appointment.objects.filter(pk=appointment.pk).exists())

    def test_provider_with_appointment_is_protected_by_service(self):
        appointment = create_appointment()

        with self.assertRaises(ProtectedError):
            appointment.provider.delete()

        self.assertTrue(Appointment.objects.filter(pk=appointment.pk).exists())


class AppointmentOpinionModelTests(TestCase):
    def test_create_opinion_for_completed_appointment(self):
        appointment = create_appointment(status=Appointment.Status.COMPLETED)

        opinion = AppointmentOpinion.objects.create(
            appointment=appointment,
            client=appointment.client,
            opinion="Good service",
            stars=5,
        )

        self.assertEqual(appointment.opinion, opinion)
        self.assertEqual(opinion.provider_response, "")
        self.assertIsNotNone(opinion.created_at)
        self.assertIsNotNone(opinion.updated_at)

    def test_appointment_can_have_only_one_opinion(self):
        appointment = create_appointment(status=Appointment.Status.COMPLETED)
        AppointmentOpinion.objects.create(
            appointment=appointment,
            client=appointment.client,
            opinion="Good service",
            stars=5,
        )

        with self.assertRaises(IntegrityError):
            AppointmentOpinion.objects.create(
                appointment=appointment,
                client=appointment.client,
                opinion="Second opinion",
                stars=4,
            )

    def test_stars_must_be_between_1_and_5(self):
        appointment = create_appointment(status=Appointment.Status.COMPLETED)
        opinion = AppointmentOpinion(
            appointment=appointment,
            client=appointment.client,
            opinion="Invalid stars",
            stars=6,
        )

        with self.assertRaises(ValidationError):
            opinion.full_clean()


class ProviderBookingSettingsModelTests(TestCase):
    def test_create_settings_with_default_slot_interval(self):
        settings = ProviderBookingSettings.objects.create(provider=ProviderFactory())

        self.assertEqual(
            settings.slot_interval_minutes,
            ProviderBookingSettings.SlotInterval.THIRTY,
        )

    def test_provider_can_have_only_one_settings_object(self):
        provider = ProviderFactory()
        ProviderBookingSettings.objects.create(provider=provider)

        with self.assertRaises(IntegrityError):
            ProviderBookingSettings.objects.create(provider=provider)

    def test_str_contains_provider_and_interval(self):
        settings = ProviderBookingSettings.objects.create(
            provider=ProviderFactory(),
            slot_interval_minutes=ProviderBookingSettings.SlotInterval.FIFTEEN,
        )

        self.assertIn("slot co 15 min", str(settings))
