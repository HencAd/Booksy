from django.core.management.base import BaseCommand

from bookings.operations import (
    mark_past_appointments_as_completed,
)


class Command(BaseCommand):
    help = "Oznacza zakończone rezerwacje jako COMPLETED."

    def handle(self, *args, **options):
        count = mark_past_appointments_as_completed()

        self.stdout.write(
            self.style.SUCCESS(f"Oznaczono {count} rezerwacji jako COMPLETED.")
        )
