import json
from datetime import date, datetime, time, timedelta

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

# we don't use gettext_lazy as it produces objects that can't be serialized by json
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_exempt
from pywebpush import WebPushException, webpush

from .forms import TemperatureForm
from .models import PushSubscription, Snooze, TemperatureRecord


def _dates_between(start_date, end_date):
    d = start_date
    res = []
    while d <= end_date:
        res.append(d)
        d += timedelta(days=1)
    return res


def index(request):
    # Determine next date to submit
    records = TemperatureRecord.objects.order_by("date")
    today = timezone.now().date()
    if not records.exists():
        initial_date = today
    else:
        first_date = records.first().date
        # Find missing dates
        dates = _dates_between(first_date, today)
        try:
            initial_date = next(d for d in dates if not records.filter(date=d).exists())
        except StopIteration:
            # All records present
            initial_date = None

    if request.method == "POST":
        # If the submitted date already exists, replace that record.
        post_date = None
        try:
            post_date = date.fromisoformat(request.POST.get("date"))
        except Exception:
            post_date = None

        existing_object = TemperatureRecord.objects.filter(date=post_date).first() if post_date else None
        # compute show_weight from the submitted date so server-side validation matches client
        show_weight = bool(post_date and post_date.weekday() == 0)
        form = TemperatureForm(request.POST, instance=existing_object)
        if form.is_valid():
            form.save()
            return redirect("temps:index")
    else:
        form = TemperatureForm(initial={"date": initial_date.isoformat()} if initial_date else None)

    # Chart data
    labels = [r.date.isoformat() for r in records]
    temps = [r.temperature for r in records]
    weights = [r.weight_kg for r in records]

    # Build a value payload to be injected via json_script
    value = {
        "labels": labels,
        "temps": temps,
        "weights": weights,
        "subscribe_url": reverse("temps:subscribe"),
        "snooze_url": reverse("temps:snooze"),
        "vapid_url": reverse("temps:vapid_public"),
    }

    return render(request, "temps/index.html", {"form": form, "initial_date": initial_date, "value": value})


def chart_data(request):
    records = TemperatureRecord.objects.order_by("date")
    data = {
        "labels": [r.date.isoformat() for r in records],
        "temps": [r.temperature for r in records],
        "weights": [r.weight_kg for r in records],
    }
    return JsonResponse(data)


@csrf_exempt
def subscribe(request):
    try:
        payload = json.loads(request.body.decode())
    except Exception:
        return HttpResponseBadRequest(_("Invalid JSON data"))
    endpoint = payload.get("endpoint")
    keys = payload.get("keys", {})
    if not endpoint:
        return HttpResponseBadRequest(_("Endpoint required"))
    PushSubscription.objects.update_or_create(
        endpoint=endpoint, defaults={"p256dh": keys.get("p256dh", ""), "auth": keys.get("auth", "")}
    )
    return JsonResponse({"status": "ok"})


def _send_push(payload):
    vapid_private = settings.VAPID_PRIVATE
    vapid_subject = settings.VAPID_SUBJECT
    subs = PushSubscription.objects.all()
    results = []
    for s in subs:
        # skip subscriptions that have an active snooze
        now = timezone.now()
        if Snooze.objects.filter(endpoint=s.endpoint, snooze_until__gte=now).exists():
            results.append({"endpoint": s.endpoint, "sent": False, "skipped": "snoozed"})
            continue
        # remove old snooze objects
        Snooze.objects.filter(endpoint=s.endpoint, snooze_until__lt=now).delete()
        sub_info = {"endpoint": s.endpoint, "keys": {"p256dh": s.p256dh, "auth": s.auth}}
        try:
            webpush(
                subscription_info=sub_info,
                data=json.dumps(payload),
                vapid_private_key=vapid_private,
                vapid_claims={"sub": vapid_subject},
            )
            results.append({"endpoint": s.endpoint, "sent": True})
        except WebPushException as e:
            try:
                data = e.response.json()
            except Exception:
                pass
            else:
                # If the subscription has been removed, delete it
                # https://autopush.readthedocs.io/en/latest/http.html#error-codes
                if data["code"] == 410 and data["errno"] == 106:
                    s.delete()
            results.append({"endpoint": s.endpoint, "sent": False, "error": str(e)})
    return results


def ping(request):
    # Called by the hourly GitHub workflow. If today's temperature missing, send push.
    if request.GET.get("token") != settings.PING_TOKEN:
        return HttpResponseBadRequest(_("Invalid token"))
    today = date.today()
    exists = TemperatureRecord.objects.filter(date=today).exists()
    if exists:
        return JsonResponse({"ok": True, "message": _("today submitted")})
    payload = {
        "title": _("Temperature reminder"),
        "body": _("You haven't submitted today's temperature yet."),
        "snooze": _("Snooze until 19:00"),
    }
    results = _send_push(payload)
    return JsonResponse({"ok": True, "sent": results})


@csrf_exempt
def snooze(request):
    try:
        payload = json.loads(request.body.decode())
    except Exception:
        return HttpResponseBadRequest(_("Invalid JSON data"))
    endpoint = payload.get("endpoint")
    if not endpoint:
        return HttpResponseBadRequest(_("Endpoint required"))

    # compute snooze until today 19:00; if past, use tomorrow 19:00
    now = timezone.now()
    snooze_until = timezone.make_aware(datetime.combine(now.date(), time(hour=19, minute=0, second=0)))

    if snooze_until <= now:
        snooze_until += timedelta(days=1)

    Snooze.objects.update_or_create(endpoint=endpoint, defaults={"snooze_until": snooze_until})
    return JsonResponse({"status": "ok", "snooze_until": snooze_until.isoformat()})


def vapid_public(request):
    # Return the VAPID public key as plain text for clients to fetch
    return HttpResponse(settings.VAPID_PUBLIC or "", content_type="text/plain")


@staff_member_required
def notify_test(request):
    """Page for admins to send a test notification to subscribers."""
    result = None
    if request.method == "POST":
        title = request.POST.get("title", "Test notification")
        body = request.POST.get("body", "This is a test notification.")
        result = _send_push({"title": title, "body": body})
    return render(request, "temps/notify_test.html", {"result": result})
