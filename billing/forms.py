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
            raise forms.ValidationError("Amount must be greater than 0.")
        return amount


class RefundForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = SecurityDeposit
        fields = ["deduction", "deduction_reason"]
        labels = {
            "deduction": "Deduction (Rs.), for damage or dues",
            "deduction_reason": "Deduction reason",
        }

    def clean_deduction(self):
        d = self.cleaned_data["deduction"]
        if d < 0:
            raise forms.ValidationError("Deduction cannot be negative.")
        if d > self.instance.amount:
            raise forms.ValidationError(f"Deduction cannot be more than the deposit (Rs. {self.instance.amount}).")
        return d

    def clean(self):
        data = super().clean()
        if data.get("deduction") and not data.get("deduction_reason"):
            self.add_error("deduction_reason", "Please enter a reason for the deduction.")
        return data