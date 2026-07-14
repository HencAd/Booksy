import factory
from django.contrib.auth.models import User

from accounts.models import Client, Provider


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ("username",)

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda user: f"{user.username}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    is_active = True
    password = factory.PostGenerationMethodCall("set_password", "password")


class ClientFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Client

    user = factory.SubFactory(UserFactory)
    phone = factory.Sequence(lambda n: f"500000{n:03d}")
    birth_date = factory.Faker("date_of_birth", minimum_age=18, maximum_age=90)


class ProviderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Provider

    user = factory.SubFactory(UserFactory)
    phone = factory.Sequence(lambda n: f"600000{n:03d}")
    business_name = factory.Sequence(lambda n: f"Provider {n}")
    bio = factory.Faker("paragraph")
    address = factory.Faker("address")
