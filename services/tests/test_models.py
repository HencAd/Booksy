from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.tests.factories import ProviderFactory
from services.models import Service
from services.tests.factories import create_service


class ServiceModelTests(TestCase):
    def test_create_service_with_required_fields(self):
        provider = ProviderFactory()
        service = Service.objects.create(
            provider=provider,
            name="Haircut",
            price=Decimal("80.00"),
            duration_minutes=45,
        )

        self.assertEqual(service.provider, provider)
        self.assertEqual(service.name, "Haircut")
        self.assertEqual(service.description, "")
        self.assertEqual(service.price, Decimal("80.00"))
        self.assertEqual(service.duration_minutes, 45)
        self.assertTrue(service.is_active)
        self.assertIsNotNone(service.created_at)
        self.assertIsNotNone(service.updated_at)

    def test_str_returns_service_name(self):
        service = create_service(name="Massage")

        self.assertEqual(str(service), "Massage")

    def test_service_is_deleted_when_provider_is_deleted(self):
        service = create_service()

        service.provider.delete()

        self.assertFalse(Service.objects.filter(pk=service.pk).exists())

    def test_name_max_length_is_200(self):
        field = Service._meta.get_field("name")

        self.assertEqual(field.max_length, 200)

    def test_duration_must_be_at_least_5_minutes(self):
        service = create_service(duration_minutes=4)

        with self.assertRaises(ValidationError) as context:
            service.full_clean()

        self.assertIn("duration_minutes", context.exception.message_dict)

    def test_duration_must_not_exceed_480_minutes(self):
        service = create_service(duration_minutes=481)

        with self.assertRaises(ValidationError) as context:
            service.full_clean()

        self.assertIn("duration_minutes", context.exception.message_dict)

    def test_price_decimal_configuration(self):
        price_field = Service._meta.get_field("price")

        self.assertEqual(price_field.max_digits, 10)
        self.assertEqual(price_field.decimal_places, 2)
