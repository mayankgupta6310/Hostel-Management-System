from django import forms

from rooms.forms import BootstrapMixin
from tenants.models import Tenant
from .models import GatePass, Visitor

DT_FORMAT = "%Y-%m-%dT%H:%M"


class GatePassForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = GatePass
        fields = ["reason", "out_time", "expected_return"]
        widgets = {
            "out_time": forms.DateTimeInput(attrs={"type": "datetime-local"}, format=DT_FORMAT),
            "expected_return": forms.DateTimeInput(attrs={"type": "datetime-local"}, format=DT_FORMAT),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["out_time"].input_formats = [DT_FORMAT]
        self.fields["expected_return"].input_formats = [DT_FORMAT]

    def clean(self):
        data = super().clean()
        out, back = data.get("out_time"), data.get("expected_return")
        if out and back and back <= out:
            raise forms.ValidationError("Wapas aane ka time nikalne ke time se baad ka hona chahiye.")
        return data


class VisitorForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Visitor
        fields = ["tenant", "visitor_name", "phone", "purpose"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # sirf wahi tenants jo abhi hostel mein hain
        self.fields["tenant"].queryset = (
            Tenant.objects.filter(allotments__is_active=True).select_related("user").distinct()
        )