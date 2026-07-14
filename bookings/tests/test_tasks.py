from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from bookings.models import Appointment
from bookings.tasks import mark_past_appointments_as_completed
from bookings.tests.factories import create_appointment


class MarkPastAppointmentsAsCompletedTests(TestCase):
    def test_marks_only_past_pending_appointments_as_completed(self):
        past_pending = create_appointment(
            start_time=timezone.now() - timedelta(hours=2),
            end_time=timezone.now() - timedelta(hours=1),
            status=Appointment.Status.PENDING,
        )
        future_pending = create_appointment(
            start_time=timezone.now() + timedelta(hours=1),
            end_time=timezone.now() + timedelta(hours=2),
            status=Appointment.Status.PENDING,
        )
        past_cancelled = create_appointment(
            start_time=timezone.now() - timedelta(hours=2),
            end_time=timezone.now() - timedelta(hours=1),
            status=Appointment.Status.CANCELLED,
        )

        updated_count = mark_past_appointments_as_completed()

        self.assertEqual(updated_count, 1)
        past_pending.refresh_from_db()
        future_pending.refresh_from_db()
        past_cancelled.refresh_from_db()
        self.assertEqual(past_pending.status, Appointment.Status.COMPLETED)
        self.assertEqual(future_pending.status, Appointment.Status.PENDING)
        self.assertEqual(past_cancelled.status, Appointment.Status.CANCELLED)
