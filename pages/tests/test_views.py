from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from services.tests.factories import create_service


class HomeViewTests(TestCase):
    def test_renders_home_page(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/home.html")

    def test_context_contains_only_active_services(self):
        active_service = create_service(name="Active service", is_active=True)
        inactive_service = create_service(name="Inactive service", is_active=False)

        response = self.client.get(reverse("home"))

        services = list(response.context["services"])
        self.assertIn(active_service, services)
        self.assertNotIn(inactive_service, services)

    def test_context_contains_six_newest_services(self):
        services = [create_service(name=f"Service {index}") for index in range(7)]

        for index, service in enumerate(services):
            service.created_at = timezone.now() + timedelta(minutes=index)
            service.save(update_fields=["created_at"])

        response = self.client.get(reverse("home"))

        self.assertEqual(
            list(response.context["services"]),
            list(reversed(services[1:])),
        )
