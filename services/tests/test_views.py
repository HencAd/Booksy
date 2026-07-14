from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.tests.factories import ClientFactory, ProviderFactory
from bookings.models import Appointment, AppointmentOpinion
from bookings.tests.factories import create_appointment
from services.models import Service
from services.tests.factories import create_service


class ServiceListViewTests(TestCase):
    def test_renders_only_active_services(self):
        active_service = create_service(name="Active service", is_active=True)
        inactive_service = create_service(name="Inactive service", is_active=False)

        response = self.client.get(reverse("service_list"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "services/service_list.html")
        self.assertIn(active_service, response.context["services"])
        self.assertNotIn(inactive_service, response.context["services"])

    def test_filters_services_by_query(self):
        matching_service = create_service(name="Haircut")
        create_service(name="Massage")

        response = self.client.get(reverse("service_list"), {"q": "hair"})

        self.assertEqual(list(response.context["services"]), [matching_service])

    def test_filters_services_by_provider_business_name(self):
        provider = ProviderFactory(business_name="Studio Alpha")
        matching_service = create_service(provider=provider, name="Consultation")
        create_service(name="Consultation")

        response = self.client.get(reverse("service_list"), {"q": "alpha"})

        self.assertEqual(list(response.context["services"]), [matching_service])

    def test_filters_services_by_price_range(self):
        cheap_service = create_service(name="Cheap", price=Decimal("50.00"))
        matching_service = create_service(name="Middle", price=Decimal("100.00"))
        expensive_service = create_service(name="Expensive", price=Decimal("150.00"))

        response = self.client.get(
            reverse("service_list"),
            {"min_price": "80", "max_price": "120"},
        )

        services = list(response.context["services"])
        self.assertEqual(services, [matching_service])
        self.assertNotIn(cheap_service, services)
        self.assertNotIn(expensive_service, services)


class ServiceDetailViewTests(TestCase):
    def test_renders_active_service_detail(self):
        service = create_service(name="Haircut")

        response = self.client.get(reverse("service_detail", args=[service.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "services/service_detail.html")
        self.assertEqual(response.context["service"], service)
        self.assertContains(response, "Haircut")

    def test_returns_404_for_inactive_service(self):
        service = create_service(is_active=False)

        response = self.client.get(reverse("service_detail", args=[service.pk]))

        self.assertEqual(response.status_code, 404)

    def test_adds_service_opinions_to_context(self):
        service = create_service()
        appointment = create_appointment(
            provider=service.provider,
            service=service,
            status=Appointment.Status.COMPLETED,
        )
        opinion = AppointmentOpinion.objects.create(
            appointment=appointment,
            client=appointment.client,
            opinion="Great",
            stars=5,
        )

        response = self.client.get(reverse("service_detail", args=[service.pk]))

        self.assertEqual(list(response.context["opinions"]), [opinion])


class ProviderServiceListViewTests(TestCase):
    def test_redirects_anonymous_user_to_login(self):
        response = self.client.get(reverse("my_service_list"))

        self.assertRedirects(
            response, f"{reverse('login')}?next={reverse('my_service_list')}"
        )

    def test_forbids_client_user(self):
        client_profile = ClientFactory()
        self.client.force_login(client_profile.user)

        response = self.client.get(reverse("my_service_list"))

        self.assertEqual(response.status_code, 403)

    def test_provider_sees_only_own_services(self):
        provider = ProviderFactory()
        own_service = create_service(provider=provider)
        create_service()
        self.client.force_login(provider.user)

        response = self.client.get(reverse("my_service_list"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "services/my_service_list.html")
        self.assertEqual(list(response.context["services"]), [own_service])


class ProviderServiceDetailViewTests(TestCase):
    def test_provider_can_open_own_service_detail(self):
        provider = ProviderFactory()
        service = create_service(provider=provider)
        self.client.force_login(provider.user)

        response = self.client.get(reverse("my_service_detail", args=[service.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "services/my_service_detail.html")
        self.assertEqual(response.context["service"], service)

    def test_provider_cannot_open_other_provider_service_detail(self):
        provider = ProviderFactory()
        other_service = create_service()
        self.client.force_login(provider.user)

        response = self.client.get(
            reverse("my_service_detail", args=[other_service.pk])
        )

        self.assertEqual(response.status_code, 404)


class ServiceCreateViewTests(TestCase):
    def test_redirects_anonymous_user_to_login(self):
        response = self.client.get(reverse("service_create"))

        self.assertRedirects(
            response, f"{reverse('login')}?next={reverse('service_create')}"
        )

    def test_forbids_client_user(self):
        client_profile = ClientFactory()
        self.client.force_login(client_profile.user)

        response = self.client.get(reverse("service_create"))

        self.assertEqual(response.status_code, 403)

    def test_provider_can_create_service(self):
        provider = ProviderFactory()
        self.client.force_login(provider.user)

        response = self.client.post(
            reverse("service_create"),
            {
                "name": "New service",
                "description": "New description",
                "price": "120.00",
                "duration_minutes": "45",
                "is_active": "on",
            },
        )

        self.assertRedirects(response, reverse("my_service_list"))
        service = Service.objects.get()
        self.assertEqual(service.provider, provider)
        self.assertEqual(service.name, "New service")
        self.assertEqual(service.description, "New description")
        self.assertEqual(service.price, Decimal("120.00"))
        self.assertEqual(service.duration_minutes, 45)
        self.assertTrue(service.is_active)

    def test_does_not_create_service_with_invalid_duration(self):
        provider = ProviderFactory()
        self.client.force_login(provider.user)

        response = self.client.post(
            reverse("service_create"),
            {
                "name": "Invalid service",
                "description": "",
                "price": "120.00",
                "duration_minutes": "4",
                "is_active": "on",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Service.objects.count(), 0)
        self.assertIn("duration_minutes", response.context["form"].errors)


class ServiceUpdateViewTests(TestCase):
    def test_provider_can_update_own_service(self):
        provider = ProviderFactory()
        service = create_service(provider=provider, name="Old name")
        self.client.force_login(provider.user)

        response = self.client.post(
            reverse("service_update", args=[service.pk]),
            {
                "name": "Updated name",
                "description": "Updated description",
                "price": "130.00",
                "duration_minutes": "90",
                "is_active": "on",
            },
        )

        self.assertRedirects(response, reverse("my_service_list"))
        service.refresh_from_db()
        self.assertEqual(service.name, "Updated name")
        self.assertEqual(service.description, "Updated description")
        self.assertEqual(service.price, Decimal("130.00"))
        self.assertEqual(service.duration_minutes, 90)
        self.assertTrue(service.is_active)

    def test_provider_cannot_update_other_provider_service(self):
        provider = ProviderFactory()
        other_service = create_service(name="Other service")
        self.client.force_login(provider.user)

        response = self.client.post(
            reverse("service_update", args=[other_service.pk]),
            {
                "name": "Updated name",
                "description": "Updated description",
                "price": "130.00",
                "duration_minutes": "90",
                "is_active": "on",
            },
        )

        self.assertEqual(response.status_code, 404)
        other_service.refresh_from_db()
        self.assertEqual(other_service.name, "Other service")


class ServiceDeactivateViewTests(TestCase):
    def test_provider_can_deactivate_own_service(self):
        provider = ProviderFactory()
        service = create_service(provider=provider, is_active=True)
        self.client.force_login(provider.user)

        response = self.client.post(reverse("service_deactivate", args=[service.pk]))

        self.assertRedirects(response, reverse("my_service_list"))
        service.refresh_from_db()
        self.assertFalse(service.is_active)

    def test_provider_cannot_deactivate_other_provider_service(self):
        provider = ProviderFactory()
        other_service = create_service(is_active=True)
        self.client.force_login(provider.user)

        response = self.client.post(
            reverse("service_deactivate", args=[other_service.pk])
        )

        self.assertEqual(response.status_code, 404)
        other_service.refresh_from_db()
        self.assertTrue(other_service.is_active)
