window.addEventListener("DOMContentLoaded", async function() {
    // Read JSON payload injected via Django's json_script
    const value = JSON.parse(document.getElementById("temps-data").textContent);

    // Read injected data
    const labels = value.labels || [];
    const temps = value.temps || [];
    const weights = value.weights || [];

    // Temperature chart
    const tctx = document.getElementById("tempChart").getContext("2d");
    new Chart(tctx, {
        type: "line",
        data: {
            labels: labels,
            datasets: [{
                label: gettext("Temperature (°C)"),
                data: temps,
                borderColor: "rgb(255, 99, 132)",
                tension: 0.2,
                fill: false,
            }]
        },
        options: {responsive: true},
    });

    // Weight chart
    const wctx = document.getElementById("weightChart").getContext("2d");
    new Chart(wctx, {
        type: "line",
        data: {
            labels: labels,
            datasets: [{
                label: gettext("Weight (kg)"),
                data: weights,
                borderColor: "rgb(54, 162, 235)",
                tension: 0.2,
                fill: false,
            }]
        },
        options: {responsive: true},
    });

    // Toggle weight field visibility based on selected date (show only on Mondays)
    function setWeightVisibility(show) {
        const weightInput = document.getElementById("id_weight_kg");
        if (!weightInput) return;
        // find wrapper (paragraph created by as_p)
        const wrapper = weightInput.closest("p") || weightInput.parentNode;
        if (show) {
            if (wrapper) wrapper.classList.remove("hidden");
            weightInput.disabled = false;
        } else {
            if (wrapper) wrapper.classList.add("hidden");
            weightInput.disabled = true;
            // clear value so it's not accidentally submitted
            try {
                weightInput.value = "";
            } catch (e) {}
        }
    }

    const dateInput = document.getElementById("id_date");
    if (dateInput) {
        const update = function () {
            const v = dateInput.value;
            if (!v) {
                setWeightVisibility(false);
                return;
            }
            // date input gives YYYY-MM-DD
            const d = new Date(v);
            // JS getDay(): 0=Sun,1=Mon
            setWeightVisibility(d.getDay() === 1);
        };
        // initialize based on current value or server hint
        // server may have rendered input with data-initially-hidden attribute
        const weightInput = document.getElementById("id_weight_kg");
        if (weightInput && weightInput.hasAttribute("data-initially-hidden")) {
            // if server asked to hide, honor that (but also allow change on date input)
            setWeightVisibility(false);
        }
        // run once
        update();
        dateInput.addEventListener("change", update);
    }

    // Push subscription
    const subscribeBtn = document.getElementById("subscribeBtn");
    const snoozeBtn = document.getElementById("snoozeBtn");
    if (!subscribeBtn) return;

    const reg = await navigator.serviceWorker.register("/static/temps/sw.js");

    async function updateButton(reg) {
        const sub = await reg.pushManager.getSubscription();
        subscribeBtn.textContent = sub ? gettext("Unsubscribe from reminders") : gettext("Enable reminder notifications");
        snoozeBtn.parentElement.classList.toggle("hidden", !sub);
    }
    await updateButton(reg);

    subscribeBtn.addEventListener("click", async () => {
        if (!("serviceWorker" in navigator) || !("PushManager" in window)) {
            alert(gettext("Push Notifications are not supported by this browser."));
            return;
        }
        const sub = await reg.pushManager.getSubscription();
        if (sub) {
            // unsubscribe locally, the server will notice it
            try {
                await sub.unsubscribe();
                alert(gettext("You are now unsubscribed from push notifications."));
            } catch (e) {
                alert(interpolate(gettext("Push unsubscription failed: %s"), [e]));
            }
            await updateButton(reg);
            return;
        }
        try {
            const permission = await Notification.requestPermission();
            if (permission !== "granted") return alert(gettext("Push Notifications permission was denied."));

            const resp = await fetch(value.vapid_url);
            const vapidPublic = await resp.text();

            const sub = await reg.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: urlBase64ToUint8Array(vapidPublic.trim()),
            });
            await fetch(
                value.subscribe_url,
                {method: "POST", body: JSON.stringify(sub), headers: {"Content-Type": "application/json"}},
            );
            alert(gettext("You are now subscribed to push notifications."));
            await updateButton(reg);
        } catch (e) {
            alert(interpolate(gettext("Push subscription failed: %s"), [e]));
        }
    });

    if (!snoozeBtn) return;
    snoozeBtn.addEventListener("click", async () => {
        try {
            const sub = await reg.pushManager.getSubscription();
            if (!sub) return;
            await fetch(value.snooze_url, {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({endpoint: sub.endpoint}),
            });
            alert(gettext("Reminder snoozed."));
        } catch (e) {
            alert(interpolate(gettext("Error while snoozing: %s"), [e]));
        }
    });
});

function urlBase64ToUint8Array(base64String) {
    const padding = "=".repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    for (let i = 0; i < rawData.length; ++i) {
        outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
}
