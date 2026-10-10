from django import forms
from .models import Room


class BootstrapMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"


class RoomCreateForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Room
        fields = ["hostel", "room_no", "floor", "capacity", "rent_per_bed"]


class RoomUpdateForm(BootstrapMixin, forms.ModelForm):
    # capacity edit nahi hogi, warna beds ka hisaab bigad sakta hai
    class Meta:
        model = Room
        fields = ["hostel", "room_no", "floor", "rent_per_bed"]