from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import DonorRegistrationForm
from .models import DonorProfile


def home(request):
    return render(request, "home.html")


def register_donor(request):
    if request.method == "POST":
        form = DonorRegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()

            DonorProfile.objects.create(
                user=user,
                blood_type=form.cleaned_data["blood_type"],
                city=form.cleaned_data["city"],
                district=form.cleaned_data["district"],
                latitude=form.cleaned_data["latitude"],
                longitude=form.cleaned_data["longitude"],
                last_donation_date=form.cleaned_data["last_donation_date"],
                consent=form.cleaned_data["consent"],
            )

            login(request, user)
            return redirect("dashboard")
    else:
        form = DonorRegistrationForm()

    return render(request, "donors/register.html", {"form": form})


@login_required
def dashboard(request):
    return render(request, "dashboard.html")
