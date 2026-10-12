from django.contrib import admin
from .models import MenuItem, MealOptOut, MessFeedback

admin.site.register(MenuItem)
admin.site.register(MealOptOut)
admin.site.register(MessFeedback)