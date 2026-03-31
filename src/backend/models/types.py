"""Pure-Python value objects for lineup events.

These dataclasses capture the complete state of a lineup — slots, DJ metadata,
and a frozen snapshot for output generation — with **zero** dependency on any
GUI framework.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import TypedDict


class DJEntry(TypedDict):
    """Shape of the DJ roster data used throughout the app."""
    name: str
    stream: str
    exact_link: bool


@dataclass
class SlotData:
    """One performer slot — pure data, no widgets."""
    name: str = ""
    genre: str = ""
    duration: int = 60


@dataclass
class DJInfo:
    """Saved DJ metadata from the library."""
    name: str = ""
    stream: str = ""
    exact_link: bool = False


@dataclass
class EventSnapshot:
    """An immutable snapshot of the full event state.

    ``OutputGenerator`` works exclusively with this — it never touches
    GUI widgets or the live model.
    """
    title: str = ""
    vol: str = ""
    group_name: str = ""
    collab: bool = False
    collab_with: str = ""
    timestamp: str = ""            # "YYYY-MM-DD HH:MM"
    genres: list[str] = field(default_factory=list)
    slots: list[SlotData] = field(default_factory=list)
    names_only: bool = False
    show_slot_genres: bool = True
    output_format: str = "discord"  # "discord" | "local"
    stream_link_format: str = ""    # "" | "quest" | "pc"
    time_dj_divider: str = " | "    # Customizable divider
    genre_divider: str = " // "     # Customizable divider
    vol_prefix: str = " VOL."       # Customizable prefix
    saved_djs: list[DJInfo] = field(default_factory=list)
    social_links: dict[str, str] = field(default_factory=dict)
    discord_embed_image: str = ""

    @property
    def start_datetime(self) -> datetime.datetime:
        """Parse ``self.timestamp`` into a ``datetime``, falling back to *now*."""
        try:
            return datetime.datetime.strptime(self.timestamp, "%Y-%m-%d %H:%M")
        except (ValueError, TypeError):
            return datetime.datetime.now()

    @property
    def full_title(self) -> str:
        base = f"{self.title}{self.vol_prefix}{self.vol}" if str(self.vol).strip() else self.title
        if self.collab and self.collab_with:
            base += f" x {self.collab_with}"
        return base
