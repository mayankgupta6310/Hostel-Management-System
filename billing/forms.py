from django import forms

from rooms.forms import BootstrapMixin
from tenants.models import Tenant
from .models import SecurityDeposit


class DepositForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = SecurityDeposit
        fields = ["tenant", "amount"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # sirf wahi tenants jinka deposit abhi tak record nahi hua
        self.fields["tenant"].queryset = (
            Tenant.objects.filter(deposit__isnull=True).select_related("user")
        )

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount <= 0:
            raise forms.ValidationError("Amount 0 se zyada hona chahiye.")
        return amount


class RefundForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = SecurityDeposit
        fields = ["deduction", "deduction_reason"]
        labels = {
            "deduction": "Deduction (Rs.), damage ya dues ke liye",
            "deduction_reason": "Deduction ka reason",
        }

    def clean_deduction(self):
        d = self.cleaned_data["deduction"]
        if d < 0:
            raise forms.ValidationError("Deduction negative nahi ho sakta.")
        if d > self.instance.amount:
            raise forms.ValidationError(f"Deduction deposit (Rs. {self.instance.amount}) se zyada nahi ho sakta.")
        return d

    def clean(self):
        data = super().clean()
        if data.get("deduction") and not data.get("deduction_reason"):
            self.add_error("deduction_reason", "Deduction hai to reason likho.")
        return data