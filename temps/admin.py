from django.contrib import admin

from .models import PushSubscription, Snooze, TemperatureRecord


@admin.register(TemperatureRecord)
class TemperatureRecordAdmin(admin.ModelAdmin):
    list_display = ("date", "temperature", "weather", "weight_kg")
    search_fields = ("notes",)


@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("endpoint", "created")


@admin.register(Snooze)
class SnoozeAdmin(admin.ModelAdmin):
    list_display = ("endpoint", "snooze_until", "created")
