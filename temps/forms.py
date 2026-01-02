from django import forms
from django.utils.translation import gettext_lazy as _

from .models import TemperatureRecord


class TemperatureForm(forms.ModelForm):
    # will be used to update yesterday's record
    yesterday_max_temp = forms.FloatField(required=False, label=_("Yesterday max temperature (°C)"))

    class Meta:
        model = TemperatureRecord
        fields = [
            "date",
            "temperature",
            "weather",
            "wind",
            "hail",
            "mist",
            "snow_cm",
            "rain_mm",
            "yesterday_max_temp",
            "notes",
            "weight_kg",
        ]
        widgets = {"date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")}
