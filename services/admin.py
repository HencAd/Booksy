from django.contrib import admin

from services.models import Service

# Register your models here.


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = [
        "provider",
        "name",
        "description",
        "price",
        "duration_minutes",
        "is_active",
        "created_at",
        "updated_at",
    ]
    list_filter = ["provider", "is_active", "price"]
    search_fields = ["name", "description"]
