from django.contrib.auth.models import User
from django.test import TestCase

from accounts.models import Client, Provider
from accounts.tests.factories import ClientFactory, ProviderFactory, UserFactory


class UserFactoryTests(TestCase):
    def test_create_user(self):
        user = UserFactory()

        self.assertEqual(User.objects.count(), 1)
        self.assertTrue(user.pk)
        self.assertTrue(user.username.startswith("user"))
        self.assertEqual(user.email, f"{user.username}@example.com")
        self.assertTrue(user.check_password("password"))

    def test_create_user_batch(self):
        users = UserFactory.create_batch(3)

        self.assertEqual(User.objects.count(), 3)
        self.assertEqual(len(users), 3)
        self.assertEqual(len({user.username for user in users}), 3)
        self.assertTrue(all(user.check_password("password") for user in users))


class ClientFactoryTests(TestCase):
    def test_create_client(self):
        client = ClientFactory()

        self.assertEqual(Client.objects.count(), 1)
        self.assertEqual(User.objects.count(), 1)
        self.assertTrue(client.pk)
        self.assertTrue(client.user.pk)
        self.assertEqual(client.user.client, client)
        self.assertTrue(client.phone.startswith("500000"))
        self.assertIsNotNone(client.birth_date)

    def test_create_client_batch(self):
        clients = ClientFactory.create_batch(3)

        self.assertEqual(Client.objects.count(), 3)
        self.assertEqual(User.objects.count(), 3)
        self.assertEqual(len(clients), 3)
        self.assertEqual(len({client.user_id for client in clients}), 3)
        self.assertEqual(len({client.phone for client in clients}), 3)


class ProviderFactoryTests(TestCase):
    def test_create_provider(self):
        provider = ProviderFactory()

        self.assertEqual(Provider.objects.count(), 1)
        self.assertEqual(User.objects.count(), 1)
        self.assertTrue(provider.pk)
        self.assertTrue(provider.user.pk)
        self.assertEqual(provider.user.provider, provider)
        self.assertTrue(provider.phone.startswith("600000"))
        self.assertTrue(provider.business_name.startswith("Provider "))
        self.assertTrue(provider.bio)
        self.assertTrue(provider.address)

    def test_create_provider_batch(self):
        providers = ProviderFactory.create_batch(3)

        self.assertEqual(Provider.objects.count(), 3)
        self.assertEqual(User.objects.count(), 3)
        self.assertEqual(len(providers), 3)
        self.assertEqual(len({provider.user_id for provider in providers}), 3)
        self.assertEqual(len({provider.phone for provider in providers}), 3)
        self.assertEqual(len({provider.business_name for provider in providers}), 3)
