from django.contrib import admin

from .models import Client, Provider


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ["user"]
    search_fields = ["user__username", "user__email"]


@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = ["user", "business_name"]
    search_fields = ["user__username", "user__email", "business_name"]
