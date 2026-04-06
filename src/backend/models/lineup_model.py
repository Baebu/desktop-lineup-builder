"""Pure-Python data model for a lineup event.

This module defines plain dataclasses that capture the *complete* state of a
lineup — titles, timestamps, slots, open-decks config, and DJ metadata — with
**zero** dependency on Tkinter or any GUI framework.

The model is the single source of truth.  UI widgets read from / write to
instance attributes, and the ``EventBus`` broadcasts changes so other
subsystems (output generation, auto-save, etc.) can react without coupling.

Typical flow
------------
1. User types in a ``CTkEntry`` → UI handler calls ``model.set_title("…")``.
2. The setter publishes ``"model_changed"`` on the bus.
3. ``OutputGenerator`` (subscribed) rebuilds the preview text.
4. The output panel (subscribed) writes the new text to the textbox.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .types import DJInfo, EventSnapshot, SlotData

if TYPE_CHECKING:
    from .event_bus import EventBus


# ── Re-export for backward compatibility ──────────────────────────────────
__all__ = ["SlotData", "DJInfo", "EventSnapshot", "LineupModel"]


# ── Live mutable model ────────────────────────────────────────────────────

class LineupModel:
    """The runtime model that backs the editor UI.

    Every mutating setter publishes ``"model_changed"`` on the bus so
    subscribers (output panel, auto-save timer, etc.) can react.

    The model is deliberately *not* a dataclass itself because it manages
    change-notification logic and provides ``snapshot()`` for consumers
    that need a frozen view.
    """

    def __init__(self, bus: EventBus) -> None:
        self._bus = bus

        self.title: str = ""
        self.vol: str = ""
        self.timestamp: str = ""
        self.genres: list[str] = []
        self.slots: list[SlotData] = []
        self.names_only: bool = False
        self.output_format: str = "discord"
        self.saved_djs: list[DJInfo] = []

    # ── Snapshot ──────────────────────────────────────────────────────

    def snapshot(self) -> EventSnapshot:
        """Return a frozen copy suitable for ``OutputGenerator``."""
        return EventSnapshot(
            title=self.title,
            vol=self.vol,
            timestamp=self.timestamp,
            genres=list(self.genres),
            slots=[SlotData(s.name, s.genre, s.club, s.duration) for s in self.slots],
            names_only=self.names_only,
            output_format=self.output_format,
            saved_djs=[DJInfo(d.name, d.stream, d.exact_link) for d in self.saved_djs],
        )

    # ── Bulk load (e.g. loading a saved event) ────────────────────────

    def load_from_dict(self, data: dict) -> None:
        """Populate the model from a plain dict (event save format)."""
        self.title = data.get("title", "")
        self.vol = data.get("vol", "")
        self.timestamp = data.get("timestamp", "")
        self.genres = list(data.get("genres", []))
        self.names_only = bool(data.get("names_only", False))
        self.slots = [
            SlotData(
                name=s.get("name", ""),
                genre=s.get("genre", ""),
                club=s.get("club", ""),
                duration=int(s.get("duration", 60)),
            )
            for s in data.get("slots", [])
        ]
        self._notify()

    def to_dict(self) -> dict:
        """Serialize to the same plain-dict format used for persistence."""
        return {
            "title": self.title,
            "vol": self.vol,
            "timestamp": self.timestamp,
            "genres": list(self.genres),
            "names_only": self.names_only,
            "slots": [
                {"name": s.name, "genre": s.genre, "club": s.club, "duration": str(s.duration)}
                for s in self.slots
            ],
        }

    # ── Change notification ───────────────────────────────────────────

    def notify(self) -> None:
        """Publicly trigger a model-changed broadcast.

        Useful when the UI has mutated a ``SlotData`` in-place and needs
        to tell subscribers about it.
        """
        self._notify()

    def _notify(self) -> None:
        self._bus.publish("model_changed")
