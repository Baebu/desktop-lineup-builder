"""Lightweight publish-subscribe event bus for decoupled communication.

Usage
-----
    bus = EventBus()
    bus.subscribe("model_changed", my_callback)
    bus.publish("model_changed", sender=some_obj)

Subscribers receive ``(event_name, **kwargs)`` so they can inspect context
without being coupled to the publisher's type.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable


class EventBus:
    """A simple, synchronous pub-sub hub.

    * **subscribe(event, callback)** — register a listener.
    * **unsubscribe(event, callback)** — remove a listener.
    * **publish(event, **kwargs)** — notify all listeners for *event*.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable[..., Any]]] = defaultdict(list)

    # ── Public API ────────────────────────────────────────────────────────

    def subscribe(self, event: str, callback: Callable[..., Any]) -> None:
        """Register *callback* for *event*.  Duplicates are silently ignored."""
        if callback not in self._subscribers[event]:
            self._subscribers[event].append(callback)

    def unsubscribe(self, event: str, callback: Callable[..., Any]) -> None:
        """Remove *callback* from *event*.  No-op if not registered."""
        try:
            self._subscribers[event].remove(callback)
        except ValueError:
            pass

    def publish(self, event: str, **kwargs: Any) -> None:
        """Call every subscriber of *event* with the supplied keyword args."""
        for cb in self._subscribers.get(event, []):
            cb(event, **kwargs)

    def clear(self) -> None:
        """Remove **all** subscriptions (useful for tests / teardown)."""
        self._subscribers.clear()
