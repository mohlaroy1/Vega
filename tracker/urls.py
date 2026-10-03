from django.urls import path
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("safety/", TemplateView.as_view(template_name="safety.html"), name="safety"),
    path("register/", views.register_donor, name="register_donor"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("requests/new/", views.create_request, name="create_request"),
    path("requests/<int:request_id>/", views.request_detail, name="request_detail"),
    path("matches/<int:match_id>/<str:response>/", views.respond_to_match, name="respond_to_match"),
]
