from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction

from rooms.forms import BootstrapMixin
from rooms.models import Bed
from .models import Tenant

User = get_user_model()


class TenantRegisterForm(BootstrapMixin, forms.ModelForm):
    username = forms.CharField(max_length=150)
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150, required=False)
    phone = forms.CharField(max_length=15)
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = Tenant
        fields = ["guardian_name", "guardian_phone", "id_proof"]

    field_order = [
        "username", "password", "first_name", "last_name", "phone",
        "guardian_name", "guardian_phone", "id_proof",
    ]

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Yeh username pehle se hai.")
        return username

    def clean_password(self):
        password = self.cleaned_data["password"]
        validate_password(password)
        return password

    def save(self, commit=True):
        d = self.cleaned_data
        with transaction.atomic():
            user = User.objects.create_user(
                username=d["username"],
                password=d["password"],
                first_name=d["first_name"],
                last_name=d["last_name"],
                phone=d["phone"],
                role="TENANT",
            )
            tenant = super().save(commit=False)
            tenant.user = user
            tenant.save()
        return tenant


class AllotmentForm(BootstrapMixin, forms.Form):
    tenant = forms.ModelChoiceField(queryset=Tenant.objects.none())
    bed = forms.ModelChoiceField(queryset=Bed.objects.none())
    start_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # sirf wahi tenant jinka koi active allotment nahi
        self.fields["tenant"].queryset = Tenant.objects.exclude(allotments__is_active=True)
        # sirf khali beds
        self.fields["bed"].queryset = Bed.objects.filter(is_occupied=False).select_related("room__hostel")