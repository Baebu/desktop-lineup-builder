"""
Pure-Python Discord bot service — no GUI imports.
Runs a discord.py client on a background thread and exposes helpers
to send messages to channels by ID.
"""

import asyncio
import threading
from typing import Callable, List, Tuple, Optional

import discord


class DiscordService:
    """Manages a Discord bot connection on a daemon thread."""

    def __init__(self) -> None:
        self._token: str = ""
        self._client: Optional[discord.Client] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._ready: threading.Event = threading.Event()
        self._on_status: Optional[Callable[[str], None]] = None  # status callback

    # ── Lifecycle ─────────────────────────────────────────────────────────

    @property
    def is_running(self) -> bool:
        return (
            self._client is not None
            and self._loop is not None
            and self._ready.is_set()
        )

    def start(self, token: str, *, on_status: Optional[Callable[[str], None]] = None) -> None:
        """Start the bot in a background thread. No-op if already running."""
        if self.is_running:
            return
        if not token.strip():
            if on_status:
                on_status("No bot token provided.")
            return

        self._token = token.strip()
        self._on_status = on_status
        self._ready.clear()

        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Gracefully shut down the bot."""
        if self._client and self._loop and not self._loop.is_closed():
            asyncio.run_coroutine_threadsafe(self._client.close(), self._loop)
        self._ready.clear()
        self._client = None
        self._loop = None
        self._thread = None
        if self._on_status:
            self._on_status("Disconnected")

    # ── Send helpers ──────────────────────────────────────────────────────

    def get_text_channels(
        self,
        *,
        on_result: Optional[Callable[[List[Tuple[str, str, int]]], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ) -> None:
        """Fetch all visible text channels from the bot's guilds."""
        if not self.is_running:
            if on_error:
                on_error("Bot is not connected.")
            return

        async def _fetch() -> None:
            try:
                results: List[Tuple[str, str, int]] = []
                if self._client:
                    for guild in self._client.guilds:
                        for ch in guild.text_channels:
                            results.append((guild.name, ch.name, ch.id))
                results.sort(key=lambda t: (t[0].lower(), t[1].lower()))
                if on_result:
                    on_result(results)
            except Exception as exc:
                if on_error:
                    on_error(str(exc))

        if self._loop:
            asyncio.run_coroutine_threadsafe(_fetch(), self._loop)

    def get_guilds(
        self,
        *,
        on_result: Optional[Callable[[List[Tuple[str, int]]], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ) -> None:
        """Fetch all visible guilds."""
        if not self.is_running:
            if on_error:
                on_error("Bot is not connected.")
            return

        async def _fetch() -> None:
            try:
                results: List[Tuple[str, int]] = []
                if self._client:
                    results = [(g.name, g.id) for g in self._client.guilds]
                results.sort(key=lambda t: t[0].lower())
                if on_result:
                    on_result(results)
            except Exception as exc:
                if on_error:
                    on_error(str(exc))

        if self._loop:
            asyncio.run_coroutine_threadsafe(_fetch(), self._loop)

    def get_roles(
        self,
        guild_id: int,
        *,
        on_result: Optional[Callable[[List[Tuple[str, int]]], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ) -> None:
        """Fetch all roles for a guild."""
        if not self.is_running:
            if on_error:
                on_error("Bot is not connected.")
            return

        async def _fetch() -> None:
            try:
                if not self._client:
                    return
                guild = self._client.get_guild(guild_id)
                if not guild:
                    raise ValueError(f"Guild {guild_id} not found.")
                results: List[Tuple[str, int]] = [(r.name, r.id) for r in guild.roles if not r.is_default()]
                results.sort(key=lambda t: t[0].lower())
                if on_result:
                    on_result(results)
            except Exception as exc:
                if on_error:
                    on_error(str(exc))

        if self._loop:
            asyncio.run_coroutine_threadsafe(_fetch(), self._loop)

    def send_message(
        self,
        channel_id: int,
        content: str,
        *,
        on_success: Optional[Callable[[], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ) -> None:
        """Queue a message send."""
        if not self.is_running:
            if on_error:
                on_error("Bot is not connected.")
            return

        async def _send() -> None:
            try:
                if not self._client:
                    return
                channel = self._client.get_channel(channel_id)
                if channel is None:
                    channel = await self._client.fetch_channel(channel_id)
                # Split into 2000-char chunks
                for i in range(0, len(content), 2000):
                    await channel.send(content[i : i + 2000])
                if on_success:
                    on_success()
            except Exception as exc:
                if on_error:
                    on_error(str(exc))

        if self._loop:
            asyncio.run_coroutine_threadsafe(_send(), self._loop)

    def send_embed(
        self,
        channel_id: int,
        embed: Optional[discord.Embed] = None,
        *,
        content: Optional[str] = None,
        file: Optional[discord.File] = None,
        on_success: Optional[Callable[[], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ) -> None:
        """Queue an embed message send, optionally with a file attachment."""
        if not self.is_running:
            if on_error:
                on_error("Bot is not connected.")
            return

        async def _send() -> None:
            try:
                if not self._client:
                    return
                channel = self._client.get_channel(channel_id)
                if channel is None:
                    channel = await self._client.fetch_channel(channel_id)
                kwargs: dict = {}
                if embed:
                    kwargs["embed"] = embed
                if content:
                    kwargs["content"] = content
                if file is not None:
                    kwargs["file"] = file
                await channel.send(**kwargs)
                if on_success:
                    on_success()
            except Exception as exc:
                if on_error:
                    on_error(str(exc))

        if self._loop:
            asyncio.run_coroutine_threadsafe(_send(), self._loop)

    # ── Internal ──────────────────────────────────────────────────────────

    def _run(self) -> None:
        """Entry point for the background thread."""
        intents = discord.Intents.default()
        intents.message_content = True
        self._client = discord.Client(intents=intents)

        @self._client.event
        async def on_ready() -> None:
            self._ready.set()
            if self._on_status and self._client:
                self._on_status(f"Connected as {self._client.user}")

        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._client.start(self._token))
        except Exception as exc:
            if self._on_status:
                self._on_status(f"Bot error: {exc}")
        finally:
            self._ready.clear()