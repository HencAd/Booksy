from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from accounts.tests.factories import ClientFactory, ProviderFactory
from bookings.models import Appointment
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


def create_appointment(client=None, provider=None, service=None, **overrides):
    service = service or create_service(provider=provider)
    start_time = timezone.now() + timedelta(days=2)
    data = {
        "client": client or ClientFactory(),
        "provider": provider or service.provider,
        "service": service,
        "start_time": start_time,
        "end_time": start_time + timedelta(minutes=service.duration_minutes),
        "status": Appointment.Status.PENDING,
    }
    data.update(overrides)
    return Appointment.objects.create(**data)
