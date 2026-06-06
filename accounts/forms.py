from typing import Any

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from accounts.models import Client, Provider


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    account_type = forms.ChoiceField(
        choices=[("client", "client"), ("provider", "provider")]
    )

    business_name = forms.CharField(max_length=200, required=False, label="Nazwa firmy")

    class Meta:
        model = User
        fields = [
            "account_type",
            "business_name",
            "username",
            "email",
            "password1",
            "password2",
        ]

    def clean(self) -> dict[Any, Any]:
        cleaned_data: dict[Any, Any] = super().clean()
        account_type = cleaned_data.get("account_type")
        business_name = cleaned_data.get("business_name")

        if account_type == "provider" and not business_name:
            self.add_error(
                "business_name", "Nazwa firmy jest wymagana dla usługodawcy."
            )

        return cleaned_data


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]


class ProfileClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ["phone", "birth_date"]


class ProfileProviderForm(forms.ModelForm):
    class Meta:
        model = Provider
        fields = ["phone", "business_name", "bio", "address"]
