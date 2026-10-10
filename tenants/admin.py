from django.contrib import admin
from .models import Tenant, Allotment

admin.site.register(Tenant)
admin.site.register(Allotment)