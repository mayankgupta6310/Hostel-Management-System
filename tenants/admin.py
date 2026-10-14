from django.contrib import admin
from .models import Tenant, Allotment, RoomChangeRequest

admin.site.register(Tenant)
admin.site.register(Allotment)
admin.site.register(RoomChangeRequest)