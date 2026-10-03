from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register_donor, name="register_donor"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("requests/new/", views.create_request, name="create_request"),
    path("requests/<int:request_id>/", views.request_detail, name="request_detail"),
]
