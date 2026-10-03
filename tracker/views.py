from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import BloodRequestForm, DonorRegistrationForm
from .matching import is_request_active
from .models import DonorProfile, Match


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
    donor_profile = DonorProfile.objects.filter(user=request.user).first()
    my_matches = None
    if donor_profile:
        my_matches = donor_profile.matches.select_related(
            "blood_request"
        ).order_by("-created_at")

    return render(
        request,
        "dashboard.html",
        {"donor_profile": donor_profile, "my_matches": my_matches},
    )


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

    return render(
        request,
        "requests/detail.html",
        {
            "blood_request": blood_request,
            "is_active": is_request_active(blood_request),
        },
    )


@login_required
def respond_to_match(request, match_id, response):
    match = get_object_or_404(Match, id=match_id)

    if request.user != match.donor.user:
        return redirect("home")

    if response == "accept":
        match.status = Match.Status.RESPONDED
    elif response == "decline":
        match.status = Match.Status.DECLINED

    match.save()
    return redirect("dashboard")
