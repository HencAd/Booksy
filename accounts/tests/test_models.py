from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from accounts.models import Client, Provider
from accounts.tests.factories import ClientFactory, ProviderFactory, UserFactory


class ClientModelTests(TestCase):
    def test_create_client_with_required_user_only(self):
        user = UserFactory()
        client = Client.objects.create(user=user)

        self.assertEqual(Client.objects.count(), 1)
        self.assertEqual(client.user, user)
        self.assertIsNone(client.phone)
        self.assertIsNone(client.birth_date)
        self.assertIsNotNone(client.created_at)
        self.assertIsNotNone(client.updated_at)

    def test_user_has_client_reverse_relation(self):
        client = ClientFactory()

        self.assertEqual(client.user.client, client)

    def test_user_relation_is_one_to_one(self):
        user = UserFactory()
        Client.objects.create(user=user)

        with self.assertRaises(IntegrityError):
            Client.objects.create(user=user)

    def test_client_is_deleted_when_user_is_deleted(self):
        client = ClientFactory()
        user = client.user

        user.delete()

        self.assertFalse(Client.objects.filter(pk=client.pk).exists())
        self.assertFalse(User.objects.filter(pk=user.pk).exists())

    def test_phone_max_length_is_11(self):
        field = Client._meta.get_field("phone")

        self.assertEqual(field.max_length, 11)

    def test_phone_cannot_exceed_max_length(self):
        client = Client(user=UserFactory(), phone="123456789012")

        with self.assertRaises(ValidationError):
            client.full_clean()

    def test_birth_date_can_be_empty(self):
        client = ClientFactory(phone="", birth_date=None)

        client.full_clean()


class ProviderModelTests(TestCase):
    def test_create_provider_with_required_fields(self):
        user = UserFactory()
        provider = Provider.objects.create(user=user, business_name="Studio Test")

        self.assertEqual(Provider.objects.count(), 1)
        self.assertEqual(provider.user, user)
        self.assertEqual(provider.business_name, "Studio Test")
        self.assertIsNone(provider.phone)
        self.assertIsNone(provider.bio)
        self.assertIsNone(provider.address)
        self.assertIsNotNone(provider.created_at)
        self.assertIsNotNone(provider.updated_at)

    def test_user_has_provider_reverse_relation(self):
        provider = ProviderFactory()

        self.assertEqual(provider.user.provider, provider)

    def test_user_relation_is_one_to_one(self):
        user = UserFactory()
        Provider.objects.create(user=user, business_name="Studio Test")

        with self.assertRaises(IntegrityError):
            Provider.objects.create(user=user, business_name="Another Studio")

    def test_provider_is_deleted_when_user_is_deleted(self):
        provider = ProviderFactory()
        user = provider.user

        user.delete()

        self.assertFalse(Provider.objects.filter(pk=provider.pk).exists())
        self.assertFalse(User.objects.filter(pk=user.pk).exists())

    def test_business_name_is_required(self):
        provider = ProviderFactory(business_name="")

        with self.assertRaises(ValidationError):
            provider.full_clean()

    def test_field_max_lengths(self):
        phone_field = Provider._meta.get_field("phone")
        business_name_field = Provider._meta.get_field("business_name")

        self.assertEqual(phone_field.max_length, 11)
        self.assertEqual(business_name_field.max_length, 200)

    def test_phone_and_business_name_cannot_exceed_max_length(self):
        provider = Provider(
            user=UserFactory(),
            phone="123456789012",
            business_name="x" * 201,
        )

        with self.assertRaises(ValidationError) as context:
            provider.full_clean()

        self.assertIn("phone", context.exception.message_dict)
        self.assertIn("business_name", context.exception.message_dict)

    def test_optional_profile_fields_can_be_empty(self):
        provider = ProviderFactory(phone="", bio="", address="")

        provider.full_clean()
