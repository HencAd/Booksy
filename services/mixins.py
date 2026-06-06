from typing import Any

from django.http import HttpRequest, HttpResponseForbidden
from django.views import View


class ProviderRequiredMixin(View):
    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseForbidden:
        if not hasattr(request.user, "provider"):
            return HttpResponseForbidden("Tylko usługodawca ma dostęp do tej strony.")

        return super().dispatch(request, *args, **kwargs)
