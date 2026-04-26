from typing import Callable, Optional, TypeAlias, TypedDict, TypeVar, TYPE_CHECKING

from i3ipc.events import IpcBaseEvent

if TYPE_CHECKING:
    from i3ipc.connection import Connection

_BaseEvent = TypeVar('_BaseEvent', bound=IpcBaseEvent, contravariant=True)

Handler: TypeAlias = Callable[['Connection', _BaseEvent], None]


class Subscription(TypedDict):
    event: str
    detail: Optional[str]
    handler: Handler


class PubSub(object):
    def __init__(self, conn: 'Connection'):
        self.conn = conn
        self._subscriptions: list[Subscription] = []

    def subscribe(self, detailed_event: str, handler: Handler):
        event = detailed_event.replace('-', '_')
        detail = ''

        if detailed_event.count('::') > 0:
            [event, detail] = detailed_event.split('::')

        self._subscriptions.append({'event': event, 'detail': detail, 'handler': handler})

    def unsubscribe(self, handler: Handler):
        self._subscriptions = list(filter(lambda s: s['handler'] != handler, self._subscriptions))

    def emit(self, event: str, data: Optional[IpcBaseEvent]):
        detail = ''

        if data and hasattr(data, 'change'):
            detail = data.change

        for s in self._subscriptions:
            if s['event'] == event:
                if not s['detail'] or s['detail'] == detail:
                    if data:
                        s['handler'](self.conn, data)
                    else:
                        s['handler'](self.conn)  # type: ignore[call-arg]
