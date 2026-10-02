from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register_donor, name="register_donor"),
    path("dashboard/", views.dashboard, name="dashboard"),
]
