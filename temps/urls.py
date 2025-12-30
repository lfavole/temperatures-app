from django.urls import path
from django.views.i18n import JavaScriptCatalog

from . import views

app_name = "temps"

urlpatterns = [
    path("chart-data", views.chart_data, name="chart_data"),
    path("jsi18n", JavaScriptCatalog.as_view(packages=["temps"]), name="javascript-catalog"),
    path("notify_test", views.notify_test, name="notify_test"),
    path("ping", views.ping, name="ping"),
    path("snooze", views.snooze, name="snooze"),
    path("subscribe", views.subscribe, name="subscribe"),
    path("vapid_public", views.vapid_public, name="vapid_public"),
    path("", views.index, name="index"),
]
