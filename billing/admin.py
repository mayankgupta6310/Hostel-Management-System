from django.contrib import admin
from .models import RentInvoice, Payment, SecurityDeposit

admin.site.register(RentInvoice)
admin.site.register(Payment)
admin.site.register(SecurityDeposit)