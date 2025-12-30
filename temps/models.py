from django.db import models
from django.utils.translation import gettext_lazy as _


class TemperatureRecord(models.Model):
    WEATHER_CHOICES = [
        ("sunny", _("Sunny")),
        ("few_clouds", _("Few clouds")),
        ("cloudy", _("Cloudy")),
        ("rain", _("Rain")),
        ("snow", _("Snow")),
    ]

    date = models.DateField(_("Date"), unique=True)
    temperature = models.FloatField(_("Temperature (°C)"))
    weather = models.CharField(_("Weather"), max_length=20, choices=WEATHER_CHOICES)
    wind = models.BooleanField(_("Wind"), default=False)
    hail = models.BooleanField(_("Hail"), default=False)
    mist = models.BooleanField(_("Mist"), default=False)
    snow_cm = models.FloatField(_("Snow (cm)"), null=True, blank=True)
    rain_mm = models.FloatField(_("Rain (mm)"), null=True, blank=True)
    max_temp = models.FloatField(_("Maximal temperature (°C)"), null=True, blank=True)
    notes = models.TextField(_("Notes"), blank=True)
    weight_kg = models.FloatField(_("Weight (kg)"), null=True, blank=True)
    created = models.DateTimeField(_("Created"), auto_now_add=True)

    def __str__(self):
        return f"{self.date} - {self.temperature}°C"

    class Meta:
        ordering = ["-date"]
        verbose_name = _("Temperature record")
        verbose_name_plural = _("Temperature records")


class PushSubscription(models.Model):
    endpoint = models.TextField(_("Endpoint"), unique=True)
    p256dh = models.CharField(_("p256dh key"), max_length=255)
    auth = models.CharField(_("Auth key"), max_length=255)
    created = models.DateTimeField(_("Created"), auto_now_add=True)

    def __str__(self):
        return self.endpoint

    class Meta:
        verbose_name = _("Push subscription")
        verbose_name_plural = _("Push subscriptions")


class Snooze(models.Model):
    """A snooze request for a push subscription: don't send pushes to `endpoint` until `snooze_until`."""

    endpoint = models.TextField(_("Endpoint"), unique=True)
    snooze_until = models.DateTimeField(_("Snooze until"))

    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.endpoint} until {self.snooze_until}"

    class Meta:
        verbose_name = _("Snooze")
        verbose_name_plural = _("Snoozes")
