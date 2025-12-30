from django import forms

from .models import TemperatureRecord


class TemperatureForm(forms.ModelForm):
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
            "max_temp",
            "notes",
            "weight_kg",
        ]
        widgets = {"date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")}
