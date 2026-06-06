from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from .forms import ProfileClientForm, ProfileProviderForm, UserForm, UserRegisterForm
from .models import Client, Provider


def register(request: HttpRequest) -> HttpResponse:

    if request.method == "POST":
        form = UserRegisterForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                user = form.save()

                account_type = form.cleaned_data.get("account_type")
                business_name = form.cleaned_data.get("business_name")

                if account_type == "client":
                    Client.objects.create(user=user)

                elif account_type == "provider":
                    Provider.objects.create(user=user, business_name=business_name)

                username = form.cleaned_data.get("username")
                messages.success(
                    request,
                    f"Konto {username} zostało utworzone! Możesz się teraz zalogować",
                )

                return redirect("login")
    else:
        form = UserRegisterForm()

    return render(request, "accounts/register.html", {"form": form})


@login_required
def profile(request: HttpRequest) -> HttpResponse:
    if hasattr(request.user, "client"):
        profile = request.user.client
        profile_type = "client"

    elif hasattr(request.user, "provider"):
        profile = request.user.provider
        profile_type = "provider"

    else:
        profile = None
        profile_type = None

    return render(
        request,
        "accounts/profile.html",
        {
            "profile": profile,
            "profile_type": profile_type,
        },
    )


@login_required
def update_profile(request: HttpRequest) -> HttpResponse:
    if hasattr(request.user, "client"):
        profile = request.user.client
        ProfileFormClass = ProfileClientForm

    elif hasattr(request.user, "provider"):
        profile = request.user.provider
        ProfileFormClass = ProfileProviderForm

    else:
        messages.error(request, "Nie znaleziono profilu użytkownika.")
        return redirect("home")

    if request.method == "POST":
        u_form = UserForm(request.POST, instance=request.user, prefix="user")
        p_form = ProfileFormClass(request.POST, instance=profile, prefix="profile")
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()

            messages.success(request, "Profil został zaktualizowany.")
            return redirect("profile")
    else:
        u_form = UserForm(instance=request.user, prefix="user")
        p_form = ProfileFormClass(instance=profile, prefix="profile")

    return render(
        request,
        "accounts/profile_edit.html",
        {
            "u_form": u_form,
            "p_form": p_form,
        },
    )
