class NotificationStream:
    def __init__(self):
        self.notifications = []

    def add_notification(self, app_name: str, title: str, text: str, priority: str = "normal"):
        item = {
            "app": app_name,
            "title": title,
            "text": text,
            "priority": priority,
            "timestamp": "Just now"
        }
        self.notifications.insert(0, item)
        # Keep latest 30 notifications
        self.notifications = self.notifications[:30]
        return item

    def get_all(self):
        return self.notifications

notification_hub = NotificationStream()
