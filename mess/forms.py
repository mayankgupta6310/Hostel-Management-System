from django import forms

from rooms.forms import BootstrapMixin
from .models import MenuItem, MessFeedback


class MenuItemForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = ["day", "meal_type", "items"]

    def validate_unique(self):
        # same din + meal dobara daalne par naya banane ki jagah update karenge (view mein)
        pass


class FeedbackForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = MessFeedback
        fields = ["meal_type", "rating", "comment"]