from datetime import time, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.tests.factories import ClientFactory, ProviderFactory
from bookings.models import (
    Appointment,
    AppointmentOpinion,
    ProviderAvailability,
    ProviderBookingSettings,
)
from bookings.tests.factories import create_appointment, create_service


class ProviderAvailabilityWeekViewTests(TestCase):
    def test_redirects_anonymous_user_to_login(self):
        response = self.client.get(reverse("my_availability"))

        self.assertRedirects(
            response, f"{reverse('login')}?next={reverse('my_availability')}"
        )

    def test_forbids_client_user(self):
        client_profile = ClientFactory()
        self.client.force_login(client_profile.user)

        response = self.client.get(reverse("my_availability"))

        self.assertEqual(response.status_code, 403)

    def test_renders_provider_week_availability(self):
        provider = ProviderFactory()
        ProviderAvailability.objects.create(
            provider=provider,
            day_of_week=ProviderAvailability.DayOfWeek.MONDAY,
            start_time=time(9, 0),
            end_time=time(17, 0),
        )
        self.client.force_login(provider.user)

        response = self.client.get(reverse("my_availability"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "bookings/my_availability_week.html")
        self.assertEqual(len(response.context["days"]), 7)
        self.assertTrue(response.context["days"][0]["is_enabled"])
        self.assertEqual(response.context["days"][0]["start_time"], "09:00")
        self.assertEqual(response.context["days"][0]["end_time"], "17:00")
        self.assertTrue(
            ProviderBookingSettings.objects.filter(provider=provider).exists()
        )

    def test_post_updates_settings_and_availability(self):
        provider = ProviderFactory()
        self.client.force_login(provider.user)

        response = self.client.post(
            reverse("my_availability"),
            {
                "slot_interval_minutes": "15",
                "day_0_enabled": "on",
                "day_0_start": "09:00",
                "day_0_end": "17:00",
            },
        )

        self.assertRedirects(response, reverse("my_availability"))
        settings = ProviderBookingSettings.objects.get(provider=provider)
        availability = ProviderAvailability.objects.get(provider=provider)
        self.assertEqual(settings.slot_interval_minutes, 15)
        self.assertEqual(
            availability.day_of_week, ProviderAvailability.DayOfWeek.MONDAY
        )
        self.assertEqual(availability.start_time, time(9, 0))
        self.assertEqual(availability.end_time, time(17, 0))


class ServiceAvailabilityViewTests(TestCase):
    def test_renders_available_slots_for_active_service(self):
        service = create_service()

        response = self.client.get(reverse("service_availability", args=[service.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "bookings/service_availability.html")
        self.assertEqual(response.context["service"], service)
        self.assertEqual(response.context["week"], 0)
        self.assertEqual(len(response.context["days"]), 7)

    def test_clamps_invalid_week_to_zero(self):
        service = create_service()

        response = self.client.get(
            reverse("service_availability", args=[service.pk]), {"week": "wrong"}
        )

        self.assertEqual(response.context["week"], 0)

    def test_clamps_week_above_one_to_one(self):
        service = create_service()

        response = self.client.get(
            reverse("service_availability", args=[service.pk]), {"week": "5"}
        )

        self.assertEqual(response.context["week"], 1)


class AppointmentCreateViewTests(TestCase):
    def test_redirects_anonymous_user_to_login(self):
        service = create_service()

        response = self.client.post(reverse("appointment_create", args=[service.pk]))

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('appointment_create', args=[service.pk])}",
        )

    def test_forbids_provider_from_creating_appointment(self):
        service = create_service()
        provider = ProviderFactory()
        self.client.force_login(provider.user)

        response = self.client.post(
            reverse("appointment_create", args=[service.pk]),
            {"start_time": (timezone.now() + timedelta(days=1)).isoformat()},
        )

        self.assertRedirects(
            response, reverse("service_availability", args=[service.pk])
        )
        self.assertEqual(Appointment.objects.count(), 0)

    def test_client_can_create_appointment(self):
        client_profile = ClientFactory()
        service = create_service(duration_minutes=45)
        start_time = timezone.now() + timedelta(days=1)
        self.client.force_login(client_profile.user)

        response = self.client.post(
            reverse("appointment_create", args=[service.pk]),
            {"start_time": start_time.isoformat()},
        )

        self.assertRedirects(response, reverse("service_detail", args=[service.pk]))
        appointment = Appointment.objects.get()
        self.assertEqual(appointment.client, client_profile)
        self.assertEqual(appointment.provider, service.provider)
        self.assertEqual(appointment.service, service)
        self.assertEqual(appointment.status, Appointment.Status.PENDING)
        self.assertEqual(
            appointment.end_time,
            appointment.start_time + timedelta(minutes=45),
        )

    def test_does_not_create_appointment_when_slot_collides(self):
        service = create_service(duration_minutes=60)
        start_time = timezone.now() + timedelta(days=1)
        create_appointment(
            provider=service.provider,
            service=service,
            start_time=start_time,
            end_time=start_time + timedelta(minutes=60),
        )
        client_profile = ClientFactory()
        self.client.force_login(client_profile.user)

        response = self.client.post(
            reverse("appointment_create", args=[service.pk]),
            {"start_time": (start_time + timedelta(minutes=30)).isoformat()},
        )

        self.assertRedirects(
            response, reverse("service_availability", args=[service.pk])
        )
        self.assertEqual(Appointment.objects.count(), 1)


class AppointmentListViewTests(TestCase):
    def test_client_sees_only_own_appointments(self):
        client_profile = ClientFactory()
        own_appointment = create_appointment(client=client_profile)
        create_appointment()
        self.client.force_login(client_profile.user)

        response = self.client.get(reverse("my_appointments"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "bookings/my_appointments.html")
        self.assertEqual(list(response.context["appointments"]), [own_appointment])

    def test_provider_sees_only_own_appointments(self):
        provider = ProviderFactory()
        service = create_service(provider=provider)
        own_appointment = create_appointment(provider=provider, service=service)
        create_appointment()
        self.client.force_login(provider.user)

        response = self.client.get(reverse("provider_appointments"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "bookings/provider_appointments.html")
        self.assertEqual(list(response.context["appointments"]), [own_appointment])

    def test_client_cannot_open_provider_appointments(self):
        client_profile = ClientFactory()
        self.client.force_login(client_profile.user)

        response = self.client.get(reverse("provider_appointments"))

        self.assertEqual(response.status_code, 403)


class AppointmentCancelViewTests(TestCase):
    def test_client_can_cancel_own_pending_appointment(self):
        appointment = create_appointment()
        self.client.force_login(appointment.client.user)

        response = self.client.post(
            reverse("appointment_cancel", args=[appointment.pk])
        )

        self.assertRedirects(response, reverse("my_appointments"))
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, Appointment.Status.CANCELLED)

    def test_client_cannot_cancel_completed_appointment(self):
        appointment = create_appointment(status=Appointment.Status.COMPLETED)
        self.client.force_login(appointment.client.user)

        response = self.client.post(
            reverse("appointment_cancel", args=[appointment.pk])
        )

        self.assertRedirects(response, reverse("my_appointments"))
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, Appointment.Status.COMPLETED)

    def test_provider_can_cancel_own_pending_appointment(self):
        appointment = create_appointment()
        self.client.force_login(appointment.provider.user)

        response = self.client.post(
            reverse("provider_appointment_cancel", args=[appointment.pk])
        )

        self.assertRedirects(response, reverse("provider_appointments"))
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, Appointment.Status.CANCELLED)


class AppointmentRescheduleViewTests(TestCase):
    def test_redirects_anonymous_user_to_login(self):
        appointment = create_appointment()

        response = self.client.get(
            reverse("appointment_reschedule", args=[appointment.pk])
        )

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('appointment_reschedule', args=[appointment.pk])}",
        )

    def test_redirects_provider_user_to_home(self):
        appointment = create_appointment()
        self.client.force_login(appointment.provider.user)

        response = self.client.get(
            reverse("appointment_reschedule", args=[appointment.pk])
        )

        self.assertRedirects(response, reverse("home"))

    def test_get_renders_pending_appointment_for_owner(self):
        appointment = create_appointment(status=Appointment.Status.PENDING)
        self.client.force_login(appointment.client.user)

        response = self.client.get(
            reverse("appointment_reschedule", args=[appointment.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "bookings/reschedule_appointments.html")
        self.assertEqual(response.context["appointment"], appointment)
        self.assertEqual(response.context["service"], appointment.service)
        self.assertEqual(response.context["week"], 0)

    def test_get_redirects_non_pending_appointment(self):
        appointment = create_appointment(status=Appointment.Status.COMPLETED)
        self.client.force_login(appointment.client.user)

        response = self.client.get(
            reverse("appointment_reschedule", args=[appointment.pk])
        )

        self.assertRedirects(response, reverse("my_appointments"))

    def test_post_updates_pending_appointment_time(self):
        appointment = create_appointment(status=Appointment.Status.PENDING)
        new_start_time = timezone.now() + timedelta(days=3)
        self.client.force_login(appointment.client.user)

        response = self.client.post(
            reverse("appointment_reschedule", args=[appointment.pk]),
            {"start_time": new_start_time.isoformat()},
        )

        self.assertRedirects(response, reverse("my_appointments"))
        appointment.refresh_from_db()
        self.assertEqual(appointment.start_time, new_start_time)
        self.assertEqual(
            appointment.end_time,
            new_start_time + timedelta(minutes=appointment.service.duration_minutes),
        )
        self.assertEqual(appointment.status, Appointment.Status.PENDING)

    def test_post_requires_start_time(self):
        appointment = create_appointment(status=Appointment.Status.PENDING)
        original_start_time = appointment.start_time
        self.client.force_login(appointment.client.user)

        response = self.client.post(
            reverse("appointment_reschedule", args=[appointment.pk]),
            {"start_time": ""},
        )

        self.assertRedirects(
            response, reverse("appointment_reschedule", args=[appointment.pk])
        )
        appointment.refresh_from_db()
        self.assertEqual(appointment.start_time, original_start_time)

    def test_post_rejects_invalid_datetime(self):
        appointment = create_appointment(status=Appointment.Status.PENDING)
        original_start_time = appointment.start_time
        self.client.force_login(appointment.client.user)

        response = self.client.post(
            reverse("appointment_reschedule", args=[appointment.pk]),
            {"start_time": "not-a-date"},
        )

        self.assertRedirects(
            response, reverse("appointment_reschedule", args=[appointment.pk])
        )
        appointment.refresh_from_db()
        self.assertEqual(appointment.start_time, original_start_time)

    def test_post_does_not_reschedule_when_slot_collides(self):
        appointment = create_appointment(status=Appointment.Status.PENDING)
        new_start_time = timezone.now() + timedelta(days=3)
        create_appointment(
            provider=appointment.provider,
            service=appointment.service,
            start_time=new_start_time + timedelta(minutes=15),
            end_time=new_start_time + timedelta(minutes=75),
            status=Appointment.Status.PENDING,
        )
        original_start_time = appointment.start_time
        self.client.force_login(appointment.client.user)

        response = self.client.post(
            reverse("appointment_reschedule", args=[appointment.pk]),
            {"start_time": new_start_time.isoformat()},
        )

        self.assertRedirects(
            response, reverse("appointment_reschedule", args=[appointment.pk])
        )
        appointment.refresh_from_db()
        self.assertEqual(appointment.start_time, original_start_time)


class AppointmentOpinionViewTests(TestCase):
    def test_client_can_create_opinion_for_completed_appointment(self):
        appointment = create_appointment(status=Appointment.Status.COMPLETED)
        self.client.force_login(appointment.client.user)

        response = self.client.post(
            reverse("appointment_opinion", args=[appointment.pk]),
            {"stars": "5", "opinion": "Great"},
        )

        self.assertRedirects(response, reverse("my_appointments"))
        opinion = AppointmentOpinion.objects.get()
        self.assertEqual(opinion.appointment, appointment)
        self.assertEqual(opinion.client, appointment.client)
        self.assertEqual(opinion.stars, 5)
        self.assertEqual(opinion.opinion, "Great")

    def test_client_cannot_create_opinion_for_pending_appointment(self):
        appointment = create_appointment(status=Appointment.Status.PENDING)
        self.client.force_login(appointment.client.user)

        response = self.client.post(
            reverse("appointment_opinion", args=[appointment.pk]),
            {"stars": "5", "opinion": "Great"},
        )

        self.assertRedirects(response, reverse("my_appointments"))
        self.assertEqual(AppointmentOpinion.objects.count(), 0)

    def test_provider_can_reply_to_opinion_for_own_service(self):
        appointment = create_appointment(status=Appointment.Status.COMPLETED)
        opinion = AppointmentOpinion.objects.create(
            appointment=appointment,
            client=appointment.client,
            opinion="Great",
            stars=5,
        )
        self.client.force_login(appointment.provider.user)

        response = self.client.post(
            reverse("provider_opinion_reply", args=[opinion.pk]),
            {"provider_response": "Thank you"},
        )

        self.assertRedirects(
            response, reverse("my_service_detail", args=[appointment.service.pk])
        )
        opinion.refresh_from_db()
        self.assertEqual(opinion.provider_response, "Thank you")

    def test_provider_cannot_add_empty_reply(self):
        appointment = create_appointment(status=Appointment.Status.COMPLETED)
        opinion = AppointmentOpinion.objects.create(
            appointment=appointment,
            client=appointment.client,
            opinion="Great",
            stars=5,
        )
        self.client.force_login(appointment.provider.user)

        response = self.client.post(
            reverse("provider_opinion_reply", args=[opinion.pk]),
            {"provider_response": "   "},
        )

        self.assertRedirects(
            response,
            reverse("my_service_detail", args=[appointment.service.pk]),
        )
        opinion.refresh_from_db()
        self.assertEqual(opinion.provider_response, "")
