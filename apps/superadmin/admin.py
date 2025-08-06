from django.contrib import admin
from .models import *
from apps.main.models import Location



admin.site.register(Administrator)
admin.site.register(Location)
# Register your models here.
