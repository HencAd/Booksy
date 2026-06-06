from typing import Any, Dict

from django.views.generic import TemplateView

from services.models import Service

# Create your views here.


class HomeView(TemplateView):
    template_name = "pages/home.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(**kwargs)

        context["services"] = (
            Service.objects.filter(is_active=True)
            .select_related("provider")
            .order_by("-created_at")[:6]
        )

        return context
