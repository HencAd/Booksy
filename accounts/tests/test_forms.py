from django.contrib.auth.models import User
from django.test import TestCase

from accounts.forms import (
    ProfileClientForm,
    ProfileProviderForm,
    UserForm,
    UserRegisterForm,
)
from accounts.tests.factories import ClientFactory, ProviderFactory, UserFactory


class UserRegisterFormTests(TestCase):
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

    def test_fields_are_in_expected_order(self):
        form = UserRegisterForm()

        self.assertEqual(
            list(form.fields),
            [
                "account_type",
                "business_name",
                "username",
                "email",
                "password1",
                "password2",
            ],
        )

    def test_client_registration_is_valid_without_business_name(self):
        form = UserRegisterForm(data=self.get_valid_data())

        self.assertTrue(form.is_valid(), form.errors)

    def test_provider_registration_requires_business_name(self):
        form = UserRegisterForm(
            data=self.get_valid_data(account_type="provider", business_name="")
        )

        self.assertFalse(form.is_valid())
        self.assertIn("business_name", form.errors)
        self.assertIn("wymagana", form.errors["business_name"][0])

    def test_provider_registration_is_valid_with_business_name(self):
        form = UserRegisterForm(
            data=self.get_valid_data(
                account_type="provider", business_name="Studio Test"
            )
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_when_passwords_do_not_match(self):
        form = UserRegisterForm(data=self.get_valid_data(password2="DifferentPass123!"))

        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)

    def test_invalid_when_username_already_exists(self):
        UserFactory(username="newuser")
        form = UserRegisterForm(data=self.get_valid_data())

        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)

    def test_save_creates_user_with_email(self):
        form = UserRegisterForm(data=self.get_valid_data())

        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()

        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(user.username, "newuser")
        self.assertEqual(user.email, "newuser@example.com")
        self.assertTrue(user.check_password("StrongPass123!"))


class UserFormTests(TestCase):
    def test_fields_are_limited_to_editable_user_profile_data(self):
        form = UserForm()

        self.assertEqual(list(form.fields), ["first_name", "last_name", "email"])

    def test_valid_data_updates_user_instance(self):
        user = UserFactory(
            first_name="Old",
            last_name="Name",
            email="old@example.com",
        )
        form = UserForm(
            data={
                "first_name": "New",
                "last_name": "Person",
                "email": "new@example.com",
            },
            instance=user,
        )

        self.assertTrue(form.is_valid(), form.errors)
        saved_user = form.save()

        self.assertEqual(saved_user.first_name, "New")
        self.assertEqual(saved_user.last_name, "Person")
        self.assertEqual(saved_user.email, "new@example.com")


class ProfileClientFormTests(TestCase):
    def test_fields_are_limited_to_client_profile_data(self):
        form = ProfileClientForm()

        self.assertEqual(list(form.fields), ["phone", "birth_date"])

    def test_valid_data_updates_client_profile(self):
        client = ClientFactory(phone="500000001", birth_date="1990-01-01")
        form = ProfileClientForm(
            data={"phone": "501002003", "birth_date": "1991-02-03"},
            instance=client,
        )

        self.assertTrue(form.is_valid(), form.errors)
        saved_client = form.save()

        self.assertEqual(saved_client.phone, "501002003")
        self.assertEqual(saved_client.birth_date.isoformat(), "1991-02-03")

    def test_optional_fields_can_be_empty(self):
        form = ProfileClientForm(data={"phone": "", "birth_date": ""})

        self.assertTrue(form.is_valid(), form.errors)


class ProfileProviderFormTests(TestCase):
    def test_fields_are_limited_to_provider_profile_data(self):
        form = ProfileProviderForm()

        self.assertEqual(
            list(form.fields),
            ["phone", "business_name", "bio", "address"],
        )

    def test_valid_data_updates_provider_profile(self):
        provider = ProviderFactory(
            phone="600000001",
            business_name="Old Studio",
            bio="Old bio",
            address="Old address",
        )
        form = ProfileProviderForm(
            data={
                "phone": "601002003",
                "business_name": "New Studio",
                "bio": "New bio",
                "address": "New address",
            },
            instance=provider,
        )

        self.assertTrue(form.is_valid(), form.errors)
        saved_provider = form.save()

        self.assertEqual(saved_provider.phone, "601002003")
        self.assertEqual(saved_provider.business_name, "New Studio")
        self.assertEqual(saved_provider.bio, "New bio")
        self.assertEqual(saved_provider.address, "New address")

    def test_business_name_is_required(self):
        form = ProfileProviderForm(
            data={
                "phone": "601002003",
                "business_name": "",
                "bio": "",
                "address": "",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("business_name", form.errors)

    def test_optional_fields_can_be_empty(self):
        form = ProfileProviderForm(
            data={
                "phone": "",
                "business_name": "Studio Test",
                "bio": "",
                "address": "",
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
