self.addEventListener("push", function(event) {
    let data = event.data.json();
    const title = data.title || "Reminder";
    const options = {
        body: data.body || "",
        icon: "/static/temps/icon.svg",
        actions: [
            {action: "snooze", title: data.snooze || "Snooze until 19:00"},
        ],
    };
    event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener("notificationclick", function(event) {
    event.notification.close();
    // If the user clicked the snooze action, register snooze on server
    if (event.action === "snooze") {
        event.waitUntil(
            (async function() {
                try {
                    const sub = await self.registration.pushManager.getSubscription();
                    if (!sub) return;
                    await fetch("/snooze", {
                        method: "POST",
                        headers: {"Content-Type": "application/json"},
                        body: JSON.stringify({endpoint: sub.endpoint}),
                    });
                } catch (e) {
                    // send a notification with the error message
                    self.registration.showNotification("Error while snoozing", {body: e});
                }
                return;
            })()
        );
        return;
    }

    event.waitUntil(clients.openWindow("/"));
});
