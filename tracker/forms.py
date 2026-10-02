from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from .models import DonorProfile


class DonorRegistrationForm(UserCreationForm):

    email = forms.EmailField(required=True, label=_("Email"))
    first_name = forms.CharField(max_length=100, label=_("Ism"))
    last_name = forms.CharField(max_length=100, label=_("Familiya"))

    blood_type = forms.ChoiceField(
        choices=DonorProfile._meta.get_field("blood_type").choices,
        label=_("Qon guruhi"),
    )

    city = forms.CharField(max_length=100, label=_("Shahar"))
    district = forms.CharField(
        max_length=100, required=False, label=_("Tuman")
    )

    latitude = forms.FloatField(
        label=_("Kenglik (latitude)"),
        help_text=_(
            "Google Maps'da joyingizni uzoq bosing va chiqqan "
            "raqamlarning birinchisini shu yerga yozing."
        ),
    )
    longitude = forms.FloatField(
        label=_("Uzunlik (longitude)"),
        help_text=_("Ikkinchi raqamni shu yerga yozing."),
    )

    last_donation_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        label=_("Oxirgi qon topshirgan sana"),
    )

    consent = forms.BooleanField(
        required=True,
        label=_(
            "Ma'lumotlarim donor sifatida kerak bo'lganda "
            "ishlatilishiga roziman."
        ),
    )

    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
        )
