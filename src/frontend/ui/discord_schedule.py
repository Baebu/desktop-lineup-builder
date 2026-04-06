import os as _os
from datetime import datetime
import dearpygui.dearpygui as dpg

from ..styling.fonts import styled_text, LABEL, MUTED, Icon, bind_icon_font
from .widgets import popup_pos

class DiscordScheduleBuilderMixin:
    """Manages the UI and background execution for scheduled Discord posts."""

    def _open_schedule_picker(self):
        """Open the calendar picker for the schedule datetime field."""
        from .date_time_picker import open_datetime_picker
        from ..types import DPGVar
        var = DPGVar(tag="discord_schedule_datetime")
        open_datetime_picker(var, callback=None)

    def _schedule_discord_post(self):
        """Add a scheduled post entry from the UI inputs."""
        raw_dt = ""
        if dpg.does_item_exist("discord_schedule_datetime"):
            raw_dt = dpg.get_value("discord_schedule_datetime").strip()
        if not raw_dt:
            self._set_discord_status("Enter a date/time to schedule.")
            return
        try:
            post_dt = datetime.strptime(raw_dt, "%Y-%m-%d %H:%M")
        except ValueError:
            self._set_discord_status("Invalid format. Use YYYY-MM-DD HH:MM")
            return
        if post_dt <= datetime.now():
            self._set_discord_status("Schedule time must be in the future.")
            return

        channel_key = "events"
        if dpg.does_item_exist("discord_schedule_channel"):
            channel_key = dpg.get_value("discord_schedule_channel")

        snap = self._build_snapshot()
        if not snap.slots:
            self._set_discord_status("Lineup is empty — nothing to schedule.")
            return

        if not hasattr(self, "_discord_scheduled_posts"):
            self._discord_scheduled_posts =[]

        body_text = dpg.get_value("output_text") if dpg.does_item_exist("output_text") else ""
        ping_roles = getattr(self, "discord_ping_roles", "").strip()
        ping_str = " ".join(f"<@&{r.strip()}>" for r in ping_roles.split(",") if r.strip())
        content_text = body_text

        entry = {
            "datetime": raw_dt,
            "channel": channel_key,
            "content": content_text,
            "ping": ping_str,
            "snapshot": snap,
            "image": getattr(self, "discord_embed_image", ""),
        }
        self._discord_scheduled_posts.append(entry)
        self._save_scheduled_posts()
        self._refresh_schedule_list_ui()
        self._set_discord_status(f"Scheduled for {raw_dt} → {channel_key}")

        if dpg.does_item_exist("discord_schedule_datetime"):
            dpg.set_value("discord_schedule_datetime", "")

    def _cancel_scheduled_post(self, idx: int):
        """Remove a scheduled post by index."""
        posts = getattr(self, "_discord_scheduled_posts",[])
        if 0 <= idx < len(posts):
            posts.pop(idx)
            self._save_scheduled_posts()
            self._refresh_schedule_list_ui()

    def _open_pending_popup(self):
        """Open a popup window showing pending scheduled posts."""
        tag = "pending_posts_win"
        if dpg.does_item_exist(tag):
            dpg.delete_item(tag)
        with dpg.window(
            tag=tag, label="Pending Scheduled Posts",
            modal=True, autosize=True, no_resize=True,
            no_scrollbar=True, min_size=(320, 100),
            pos=popup_pos("discord_pending_btn", width=320, height=200),
        ):
            dpg.add_group(tag="discord_scheduled_list")
            self._refresh_schedule_list_ui()
            dpg.add_spacer(height=4)
            dpg.add_button(label="Close", width=-1,
                           callback=lambda: dpg.delete_item(tag))

    def _refresh_schedule_list_ui(self):
        """Rebuild the pending-posts list in the popup."""
        tag = "discord_scheduled_list"
        if not dpg.does_item_exist(tag):
            return
        dpg.delete_item(tag, children_only=True)

        posts = getattr(self, "_discord_scheduled_posts",[])
        if not posts:
            styled_text("  No scheduled posts", MUTED, parent=tag)
            return

        for i, entry in enumerate(posts):
            dt_str = entry.get("datetime", "?")
            ch = entry.get("channel", "?")
            with dpg.group(horizontal=True, parent=tag):
                styled_text(f"  {dt_str} → {ch}", LABEL)
                idx = i  # capture for closure
                dpg.add_button(
                    label=Icon.CLOSE, width=22, height=18,
                    callback=lambda s, a, u=idx: self._cancel_scheduled_post(u),
                )
                bind_icon_font(dpg.last_item())

    def check_scheduled_posts(self):
        """Called every frame via process_queue to fire due posts."""
        now = datetime.now()
        last = getattr(self, "_last_schedule_check", None)
        if last and (now - last).total_seconds() < 1.0:
            return
        self._last_schedule_check = now

        posts = getattr(self, "_discord_scheduled_posts",[])
        if not posts:
            return

        fired =[]
        for i, entry in enumerate(posts):
            try:
                post_dt = datetime.strptime(entry["datetime"], "%Y-%m-%d %H:%M")
            except (ValueError, KeyError):
                fired.append(i)
                continue
            if now >= post_dt:
                self._fire_scheduled_post(entry)
                fired.append(i)

        if fired:
            for idx in reversed(fired):
                posts.pop(idx)
            self._save_scheduled_posts()
            self._refresh_schedule_list_ui()

    def _fire_scheduled_post(self, entry: dict):
        """Execute a scheduled post using its stored snapshot."""
        import datetime as _dt
        import discord

        channel_key = entry.get("channel", "events")
        if not self._discord_service.is_running:
            self._set_discord_status(f"Missed schedule ({channel_key}): bot not connected.")
            return

        channel_id_str = self.discord_channels.get(channel_key, "").strip()
        if not channel_id_str:
            self._set_discord_status(f"Missed schedule: no channel for '{channel_key}'.")
            return
        try:
            channel_id = int(channel_id_str)
        except ValueError:
            self._set_discord_status(f"Missed schedule: invalid channel for '{channel_key}'.")
            return

        snap = entry.get("snapshot")
        if snap is None or not snap.slots:
            return

        start = snap.start_datetime
        unix = int(start.timestamp())

        embed = discord.Embed(
            title=snap.full_title or "Lineup",
            description=f"<t:{unix}:F> (<t:{unix}:R>)",
            color=0x5865F2,
            timestamp=_dt.datetime.fromtimestamp(unix, tz=_dt.timezone.utc),
        )

        if snap.genres:
            genre_div = getattr(snap, "genre_divider", " // ")
            embed.add_field(name="Genres", value=genre_div.join(snap.genres), inline=False)

        ptr = start
        lineup_lines: list[str] =[]
        
        dj_div = getattr(snap, "time_dj_divider", " | ")
        
        for slot in snap.slots:
            name = slot.name or "TBA"
            if snap.names_only:
                lineup_lines.append(f"**{name}**")
            else:
                ts = int(ptr.timestamp())
                genre_str = f"  •  {slot.genre}" if slot.genre else ""
                lineup_lines.append(f"<t:{ts}:t>{dj_div}**{name}**{genre_str}")
            ptr += _dt.timedelta(minutes=slot.duration)

        lineup_text = "\n".join(lineup_lines)
        chunks = [lineup_text[i : i + 1024] for i in range(0, len(lineup_text), 1024)]
        for i, chunk in enumerate(chunks):
            embed.add_field(
                name="Lineup" if i == 0 else "\u200b",
                value=chunk, inline=False,
            )

        link_order =["TIMELINE", "VRCPOP", "X", "IG", "DISCORD", "VRC GROUP"]
        if snap.social_links:
            parts = [
                f"[{label}]({snap.social_links[label]})"
                for label in link_order
                if snap.social_links.get(label, "").strip()
            ]
            if parts:
                embed.add_field(name="Links", value=" | ".join(parts), inline=False)

        image_path = entry.get("image", "").strip()
        attach_file = None
        if image_path:
            if image_path.startswith(("http://", "https://")):
                embed.set_image(url=image_path)
            elif _os.path.isfile(image_path):
                ext = _os.path.splitext(image_path)[1]
                safe_name = f"image{ext}"
                attach_file = discord.File(image_path, filename=safe_name)
                embed.set_image(url=f"attachment://{safe_name}")

        embed.set_footer(text="GitHub | Baebu/lineup_builder")

        ping_content = entry.get("ping", "")
        if ping_content:
             embed.description = f"{embed.description}\n\n{ping_content}"

        self._set_discord_status(f"Sending scheduled post to {channel_key}...")
        self._discord_service.send_embed(
            channel_id, embed,
            content=entry.get("content", ""),
            file=attach_file,
            on_success=lambda: self._set_discord_status(
                f"Scheduled post sent to {channel_key}."),
            on_error=lambda e: self._set_discord_status(f"Schedule error: {e}"),
        )

    def _save_scheduled_posts(self):
        """Persist scheduled posts to settings.json."""
        from ..types import DPGVar  # noqa: F401
        posts = getattr(self, "_discord_scheduled_posts",[])
        serializable =[]
        for entry in posts:
            serializable.append({
                "datetime": entry.get("datetime", ""),
                "channel": entry.get("channel", ""),
                "content": entry.get("content", ""),
                "ping": entry.get("ping", ""),
                "image": entry.get("image", ""),
                "snapshot": self._snapshot_to_dict(entry.get("snapshot"))
                            if entry.get("snapshot") else None,
            })
        self.discord_scheduled_posts = serializable
        self.save_settings()

    @staticmethod
    def _snapshot_to_dict(snap) -> dict:
        """Serialize an EventSnapshot to a plain dict."""
        if snap is None:
            return {}
        return {
            "title": snap.title,
            "vol": snap.vol,
            "timestamp": snap.timestamp,
            "genres": list(snap.genres),
            "slots":[{"name": s.name, "genre": s.genre, "club": s.club, "duration": s.duration}
                      for s in snap.slots],
            "names_only": snap.names_only,
            "output_format": snap.output_format,
            "time_dj_divider": getattr(snap, "time_dj_divider", " | "),
            "genre_divider": getattr(snap, "genre_divider", " // "),
            "vol_prefix": getattr(snap, "vol_prefix", " VOL."),
            "saved_djs":[{"name": d.name, "stream": d.stream, "exact_link": d.exact_link}
                          for d in snap.saved_djs],
            "social_links": dict(snap.social_links),
        }

    @staticmethod
    def _dict_to_snapshot(d: dict):
        """Deserialize a plain dict back into an EventSnapshot."""
        from ...backend.models.types import DJInfo, EventSnapshot, SlotData
        if not d:
            return None
        return EventSnapshot(
            title=d.get("title", ""),
            vol=d.get("vol", ""),
            timestamp=d.get("timestamp", ""),
            genres=d.get("genres", []),
            slots=[SlotData(s.get("name", ""), s.get("genre", ""), s.get("club", ""), s.get("duration", 60))
                   for s in d.get("slots", [])],
            names_only=d.get("names_only", False),
            output_format=d.get("output_format", "discord"),
            time_dj_divider=d.get("time_dj_divider", " | "),
            genre_divider=d.get("genre_divider", " // "),
            vol_prefix=d.get("vol_prefix", " VOL."),
            saved_djs=[DJInfo(dj.get("name", ""), dj.get("stream", ""), dj.get("exact_link", False))
                       for dj in d.get("saved_djs", [])],
            social_links=d.get("social_links", {}),
        )

    def _load_scheduled_posts(self):
        """Restore scheduled posts from settings (called at startup)."""
        self._discord_scheduled_posts =[]
        raw = getattr(self, "discord_scheduled_posts",[])
        now = datetime.now()
        for entry in raw:
            try:
                post_dt = datetime.strptime(entry["datetime"], "%Y-%m-%d %H:%M")
            except (ValueError, KeyError):
                continue
            if post_dt > now:
                snap = self._dict_to_snapshot(entry.get("snapshot"))
                self._discord_scheduled_posts.append({
                    "datetime": entry["datetime"],
                    "channel": entry.get("channel", "events"),
                    "content": entry.get("content", ""),
                    "snapshot": snap,
                })