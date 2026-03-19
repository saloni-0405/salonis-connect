from django.contrib import admin
from .models import Category, Worker, Booking, Payment, CustomerLead

admin.site.register(Category)
admin.site.register(Worker)
admin.site.register(Booking)
admin.site.register(Payment)
admin.site.register(CustomerLead)