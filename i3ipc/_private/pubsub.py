class PubSub(object):
    def __init__(self, conn):
        self.conn = conn
        self._subscriptions = []

    def subscribe(self, detailed_event, handler):
        event = detailed_event.replace('-', '_')
        detail = ''

        if detailed_event.count('::') > 0:
            [event, detail] = detailed_event.split('::')

        self._subscriptions.append({'event': event, 'detail': detail, 'handler': handler})

    def unsubscribe(self, handler):
        self._subscriptions = list(filter(lambda s: s['handler'] != handler, self._subscriptions))

    def emit(self, event, data):
        detail = ''

        if data and hasattr(data, 'change'):
            detail = data.change

        for s in self._subscriptions:
            if s['event'] == event:
                if not s['detail'] or s['detail'] == detail:
                    if data:
                        s['handler'](self.conn, data)
                    else:
                        s['handler'](self.conn)
