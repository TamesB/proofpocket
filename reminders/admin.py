from django.contrib import admin
from .models import ReminderEvent
from .models import ReminderRule
# Register your models here.
admin.site.register(ReminderEvent)
admin.site.register(ReminderRule)