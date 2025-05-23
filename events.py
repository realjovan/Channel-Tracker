# events that objects can subscribe to and receive notifications
class Event:
    def __init__(self):
        self.subscribers = []

    def subscribe(self, subscriber):
        self.subscribers.append(subscriber)

    def unsubscribe(self, subscriber):
        self.subscribers.remove(subscriber)

    def notify(self, *args, **kwargs):
        for subscriber in self.subscribers:
            subscriber(*args, **kwargs)

# events
app_launched = Event()
channel_went_live = Event()
channel_went_offline = Event()
gui_hidden = Event()
gui_shown = Event()
search_error = Event()