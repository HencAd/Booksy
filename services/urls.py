from django.urls import path

from . import views

urlpatterns = [
    path("services/", views.ServiceListView.as_view(), name="service_list"),
    path(
        "services/<int:pk>/", views.ServiceDetailView.as_view(), name="service_detail"
    ),
    path(
        "my-services/", views.ProviderServiceListView.as_view(), name="my_service_list"
    ),
    path("my-services/add/", views.ServiceCreateView.as_view(), name="service_create"),
    path(
        "my-services/<int:pk>/",
        views.ProviderServiceDetailView.as_view(),
        name="my_service_detail",
    ),
    path(
        "my-services/<int:pk>/edit/",
        views.ServiceUpdateView.as_view(),
        name="service_update",
    ),
    path(
        "my-services/<int:pk>/deactivate/",
        views.ServiceDeactivateView.as_view(),
        name="service_deactivate",
    ),
]
