from decimal import Decimal

from accounts.tests.factories import ProviderFactory
from services.models import Service


def create_service(provider=None, **overrides):
    data = {
        "provider": provider or ProviderFactory(),
        "name": "Test service",
        "description": "Test description",
        "price": Decimal("100.00"),
        "duration_minutes": 60,
        "is_active": True,
    }
    data.update(overrides)
    return Service.objects.create(**data)
