from django import forms
from rooms.forms import BootstrapMixin
from .models import Complaint


class ComplaintForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ["category", "title", "description", "image"]
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}