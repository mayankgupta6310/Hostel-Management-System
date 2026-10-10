from django.contrib import admin
from .models import RentInvoice, Payment

admin.site.register(RentInvoice)
admin.site.register(Payment)