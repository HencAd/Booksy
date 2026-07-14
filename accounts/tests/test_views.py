from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import Client, Provider
from accounts.tests.factories import ClientFactory, ProviderFactory, UserFactory


class ProfileViewTests(TestCase):
    def test_redirects_anonymous_user_to_login(self):
        response = self.client.get(reverse("profile"))

        self.assertRedirects(response, f"{reverse('login')}?next={reverse('profile')}")

    def test_renders_client_profile(self):
        client_profile = ClientFactory(
            user__username="client_user",
            user__email="client@example.com",
            phone="500111222",
        )
        self.client.force_login(client_profile.user)

        response = self.client.get(reverse("profile"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/profile.html")
        self.assertEqual(response.context["profile"], client_profile)
        self.assertEqual(response.context["profile_type"], "client")
        self.assertContains(response, "client_user")
        self.assertContains(response, "client@example.com")
        self.assertContains(response, "500111222")

    def test_renders_provider_profile(self):
        provider_profile = ProviderFactory(
            user__username="provider_user",
            user__email="provider@example.com",
            phone="600111222",
            business_name="Studio Test",
            address="Test address",
            bio="Test bio",
        )
        self.client.force_login(provider_profile.user)

        response = self.client.get(reverse("profile"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/profile.html")
        self.assertEqual(response.context["profile"], provider_profile)
        self.assertEqual(response.context["profile_type"], "provider")
        self.assertContains(response, "provider_user")
        self.assertContains(response, "provider@example.com")
        self.assertContains(response, "Studio Test")
        self.assertContains(response, "Test address")
        self.assertContains(response, "600111222")
        self.assertContains(response, "Test bio")

    def test_renders_empty_profile_state_for_user_without_profile(self):
        user = UserFactory(username="plain_user")
        self.client.force_login(user)

        response = self.client.get(reverse("profile"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/profile.html")
        self.assertIsNone(response.context["profile"])
        self.assertIsNone(response.context["profile_type"])
        self.assertContains(response, "Nie znaleziono profilu")


class RegisterViewTests(TestCase):
    def get_valid_data(self, **overrides):
        data = {
            "account_type": "client",
            "business_name": "",
            "username": "newuser",
            "email": "newuser@example.com",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        }
        data.update(overrides)
        return data

    def test_get_renders_register_form(self):
        response = self.client.get(reverse("register"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/register.html")
        self.assertIn("form", response.context)

    def test_creates_client_account(self):
        response = self.client.post(reverse("register"), self.get_valid_data())

        self.assertRedirects(response, reverse("login"))
        user = User.objects.get(username="newuser")
        self.assertEqual(user.email, "newuser@example.com")
        self.assertTrue(hasattr(user, "client"))
        self.assertFalse(hasattr(user, "provider"))
        self.assertEqual(Client.objects.count(), 1)

    def test_creates_provider_account(self):
        response = self.client.post(
            reverse("register"),
            self.get_valid_data(
                account_type="provider",
                business_name="Studio Test",
            ),
        )

        self.assertRedirects(response, reverse("login"))
        user = User.objects.get(username="newuser")
        self.assertTrue(hasattr(user, "provider"))
        self.assertEqual(user.provider.business_name, "Studio Test")
        self.assertEqual(Provider.objects.count(), 1)

    def test_does_not_create_provider_without_business_name(self):
        response = self.client.post(
            reverse("register"),
            self.get_valid_data(account_type="provider", business_name=""),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), 0)
        self.assertIn("business_name", response.context["form"].errors)


class UpdateProfileViewTests(TestCase):
    def test_redirects_anonymous_user_to_login(self):
        response = self.client.get(reverse("profile_edit"))

        self.assertRedirects(
            response, f"{reverse('login')}?next={reverse('profile_edit')}"
        )

    def test_get_renders_client_profile_forms(self):
        client_profile = ClientFactory()
        self.client.force_login(client_profile.user)

        response = self.client.get(reverse("profile_edit"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/profile_edit.html")
        self.assertEqual(response.context["u_form"].prefix, "user")
        self.assertEqual(response.context["p_form"].prefix, "profile")

    def test_updates_client_profile(self):
        client_profile = ClientFactory(
            user__first_name="Old",
            user__last_name="Name",
            user__email="old@example.com",
            phone="500000001",
        )
        self.client.force_login(client_profile.user)

        response = self.client.post(
            reverse("profile_edit"),
            {
                "user-first_name": "New",
                "user-last_name": "Person",
                "user-email": "new@example.com",
                "profile-phone": "501002003",
                "profile-birth_date": "1990-01-02",
            },
        )

        self.assertRedirects(response, reverse("profile"))
        client_profile.refresh_from_db()
        client_profile.user.refresh_from_db()
        self.assertEqual(client_profile.user.first_name, "New")
        self.assertEqual(client_profile.user.last_name, "Person")
        self.assertEqual(client_profile.user.email, "new@example.com")
        self.assertEqual(client_profile.phone, "501002003")
        self.assertEqual(client_profile.birth_date.isoformat(), "1990-01-02")

    def test_updates_provider_profile(self):
        provider_profile = ProviderFactory(
            user__email="old@example.com",
            phone="600000001",
            business_name="Old Studio",
            bio="Old bio",
            address="Old address",
        )
        self.client.force_login(provider_profile.user)

        response = self.client.post(
            reverse("profile_edit"),
            {
                "user-first_name": "New",
                "user-last_name": "Provider",
                "user-email": "provider@example.com",
                "profile-phone": "601002003",
                "profile-business_name": "New Studio",
                "profile-bio": "New bio",
                "profile-address": "New address",
            },
        )

        self.assertRedirects(response, reverse("profile"))
        provider_profile.refresh_from_db()
        provider_profile.user.refresh_from_db()
        self.assertEqual(provider_profile.user.email, "provider@example.com")
        self.assertEqual(provider_profile.phone, "601002003")
        self.assertEqual(provider_profile.business_name, "New Studio")
        self.assertEqual(provider_profile.bio, "New bio")
        self.assertEqual(provider_profile.address, "New address")

    def test_redirects_user_without_profile_to_home(self):
        user = UserFactory()
        self.client.force_login(user)

        response = self.client.get(reverse("profile_edit"))

        self.assertRedirects(response, reverse("home"))
