from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import BloodRequestForm, DonorRegistrationForm
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


@login_required
def create_request(request):
    if request.method == "POST":
        form = BloodRequestForm(request.POST)

        if form.is_valid():
            blood_request = form.save(commit=False)
            blood_request.requester = request.user
            blood_request.save()
            return redirect("request_detail", request_id=blood_request.id)
    else:
        form = BloodRequestForm()

    return render(request, "requests/create.html", {"form": form})


@login_required
def request_detail(request, request_id):
    from .models import BloodRequest
    from django.shortcuts import get_object_or_404

    blood_request = get_object_or_404(BloodRequest, id=request_id)

    is_owner = blood_request.requester_id == request.user.id
    is_staff = request.user.is_staff

    if not (is_owner or is_staff):
        return redirect("home")

    return render(request, "requests/detail.html", {"blood_request": blood_request})
