from django.http import HttpResponseForbidden


class ProviderRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, "provider"):
            return HttpResponseForbidden("Tylko usługodawca ma dostęp do tej strony.")

        return super().dispatch(request, *args, **kwargs)
