import os as _os
import dearpygui.dearpygui as dpg

from ..styling.fonts import styled_text, LABEL, MUTED, Icon, bind_icon_font
from .widgets import add_primary_button, popup_pos
from .confirm_dialog import confirm
from .toast import show_toast

class DiscordBuilderMixin:
    def _save_discord_credentials(self):
        """Persist client ID from the input field."""
        if dpg.does_item_exist("discord_client_id"):
            self.discord_client_id = dpg.get_value("discord_client_id").strip()
        self.save_settings()

    def _save_discord_ping_roles(self):
        if dpg.does_item_exist("discord_ping_roles"):
            display = dpg.get_value("discord_ping_roles")
            role_map = getattr(self, "_discord_role_map", {})
            self.discord_ping_roles = str(role_map.get(display, ""))
        self.save_settings()

    def _invite_discord_bot(self):
        """Open the bot invite URL in the browser."""
        client_id = getattr(self, "discord_client_id", "")
        if dpg.does_item_exist("discord_client_id"):
            client_id = dpg.get_value("discord_client_id").strip()
        if not client_id:
            self._set_discord_status("No Client ID provided.")
            return
        invite_url = (
            f"https://discord.com/oauth2/authorize"
            f"?client_id={client_id}&permissions=67584&scope=bot"
        )
        import webbrowser
        webbrowser.open(invite_url)

    def _open_bot_guide(self):
        """Displays a modal with instructions for Discord bot setup."""
        win_tag = "bot_guide_win"
        if dpg.does_item_exist(win_tag):
            dpg.delete_item(win_tag)
        
        with dpg.window(tag=win_tag, label="Discord Bot Guide", modal=True,
                        width=500, height=450, no_resize=True,
                        pos=popup_pos(width=500, height=450)):
            styled_text("HOW TO SETUP YOUR DISCORD BOT", LABEL)
            dpg.add_separator()
            dpg.add_spacer(height=8)
            
            guide = (
                "1. Go to: https://discord.com/developers/applications\n"
                "2. Click 'New Application' and name it.\n"
                "3. In the 'General Information' tab, copy your CLIENT ID.\n"
                "4. Go to the 'Bot' tab on the left sidebar.\n"
                "5. Enable 'Message Content Intent' under Privileged Gateway Intents.\n"
                "6. Click 'Reset Token' to get your BOT TOKEN. (Save this, it's secret!)\n"
                "7. Invite the bot to your server using the 'Invite Bot' button here."
            )
            dpg.add_text(guide, wrap=480)
            
            dpg.add_spacer(height=16)
            add_primary_button("Got it", width=-1, callback=lambda: dpg.delete_item(win_tag))

    def _clear_embed_image(self):
        """Clear the embed image."""
        self.discord_embed_image = ""
        if dpg.does_item_exist("embed_image_browse_btn"):
            dpg.set_item_label("embed_image_browse_btn", "Select Image...")
        
        # Clear the displayed image
        tex_tag = "embed_image_tex"
        if dpg.does_item_exist(tex_tag):
            dpg.delete_item(tex_tag)
        if dpg.does_item_exist("embed_image_display"):
            dpg.delete_item("embed_image_display")
            
        self._schedule_update()

    def _browse_embed_image(self):
        """Open the native Windows file explorer to pick a local image."""
        import tkinter as _tk
        from tkinter import filedialog as _fd
        root = _tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        path = _fd.askopenfilename(
            parent=root,
            title="Select Embed Image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.gif *.webp"),
                ("All files", "*.*"),
            ],
        )
        root.destroy()
        if path:
            self.discord_embed_image = path
            if dpg.does_item_exist("embed_image_browse_btn"):
                label = _os.path.basename(path)
                if len(label) > 32:
                    label = label[:29] + "..."
                dpg.set_item_label("embed_image_browse_btn", label)
            
            # Clear existing image display so it gets refreshed
            tex_tag = "embed_image_tex"
            if dpg.does_item_exist(tex_tag):
                dpg.delete_item(tex_tag)
            if dpg.does_item_exist("embed_image_display"):
                dpg.delete_item("embed_image_display")
                
            self._schedule_update()

    def _build_discord_settings_drawer(self):
        """Populate the Discord settings drawer with bot config fields."""
        styled_text("  Client ID", LABEL)
        dpg.add_input_text(
            tag="discord_client_id",
            default_value=getattr(self, "discord_client_id", ""),
            hint="Application Client ID...",
            width=-1,
            callback=lambda s, a, u=None: self._save_discord_credentials(),
        )
        dpg.add_spacer(height=2)
        styled_text("  Bot Token", LABEL)
        dpg.add_input_text(
            tag="discord_bot_token",
            default_value=getattr(self, "discord_bot_token", ""),
            hint="Paste bot token here...",
            password=True,
            width=-1,
            callback=lambda s, a, u=None: self._save_bot_token(),
        )
        dpg.add_spacer(height=4)
        
        # Action buttons
        add_primary_button("Invite Bot to Server", width=-1, callback=lambda: self._invite_discord_bot())
        dpg.add_spacer(height=2)
        dpg.add_button(label="Guide", width=-1, callback=lambda: self._open_bot_guide())

    def _toggle_discord_settings_drawer(self):
        """Toggle the inline Discord settings drawer open/closed."""
        tag = "discord_settings_drawer"
        if not dpg.does_item_exist(tag):
            return
        currently_shown = dpg.is_item_shown(tag)
        dpg.configure_item(tag, show=not currently_shown)

    def _filter_combo(self, sender, app_data, user_data):
        """Generic filter for combo boxes."""
        combo_tag, items_list = user_data
        query = app_data.lower()
        filtered = [item for item in items_list if query in item.lower()]
        dpg.configure_item(combo_tag, items=filtered)

    def _on_server_selected(self):
        """When server combo changes, save and fetch channels + roles."""
        if dpg.does_item_exist("discord_ping_server"):
            display = dpg.get_value("discord_ping_server")
            guild_map = getattr(self, "_discord_guild_map", {})
            guild_id = str(guild_map.get(display, ""))
            self.discord_ping_server = guild_id
            self.save_settings()
            if guild_id:
                self._fetch_discord_roles(guild_id)
                self._fetch_discord_channels_for_guild(guild_id)
            else:
                dpg.configure_item("discord_ping_roles", items=["None"])
                dpg.set_value("discord_ping_roles", "None")
                self.discord_ping_roles = ""
                dpg.configure_item("discord_channel", items=[])
                dpg.set_value("discord_channel", "")
                self.save_settings()

    def _save_discord_channel(self):
        """Read Discord channel combo selection and persist channel ID."""
        channel_map = getattr(self, "_discord_channel_map", {})
        tag = "discord_channel"
        if dpg.does_item_exist(tag):
            display = dpg.get_value(tag).strip()
            self.discord_channel_id = str(channel_map.get(display, ""))
        self.save_settings()

    def _channel_display(self, channel_id_str: str) -> str:
        """Return the display string for a saved channel ID, or empty."""
        channel_map = getattr(self, "_discord_channel_map", {})
        for display, cid in channel_map.items():
            if str(cid) == channel_id_str:
                return display
        return ""

    def _fetch_discord_channels_for_guild(self, guild_id_str: str):
        """Ask the bot to list text channels for a specific guild."""
        if not self._discord_service.is_running:
            self._set_discord_status("Connect bot first.")
            return
        self._discord_service.get_text_channels(
            on_result=lambda channels: self._queue_on_main(
                lambda: self._on_channels_fetched(channels, guild_id_str)),
            on_error=lambda e: self._set_discord_status(f"Error: {e}"),
        )

    def _on_channels_fetched(self, channels: list[tuple[str, str, int]], guild_id_str: str = ""):
        """Populate the single channel combo with fetched data."""
        items = []
        channel_map: dict[str, int] = {}
        for guild_name, ch_name, ch_id in channels:
            # If we know the guild, filter to only that guild's channels
            if guild_id_str:
                guild_map = getattr(self, "_discord_guild_map", {})
                matched = False
                for g_display, g_id in guild_map.items():
                    if str(g_id) == guild_id_str and g_display == guild_name:
                        matched = True
                        break
                if not matched:
                    continue
            display = f"#{ch_name}"
            items.append(display)
            channel_map[display] = ch_id

        self._discord_channel_map = channel_map
        self._discord_channel_items = items

        tag = "discord_channel"
        if dpg.does_item_exist(tag):
            dpg.configure_item(tag, items=items)
            saved_id = getattr(self, "discord_channel_id", "")
            current = ""
            for display, cid in channel_map.items():
                if str(cid) == saved_id:
                    current = display
                    break
            dpg.set_value(tag, current)

    def _fetch_discord_guilds(self):
        """Ask the bot to list all visible guilds."""
        if not self._discord_service.is_running:
            return
        self._discord_service.get_guilds(
            on_result=lambda guilds: self._queue_on_main(
                lambda: self._on_guilds_fetched(guilds)),
            on_error=lambda e: self._set_discord_status(f"Error: {e}"),
        )

    def _on_guilds_fetched(self, guilds: list[tuple[str, int]]):
        items =[]
        guild_map = {}
        for g_name, g_id in guilds:
            items.append(g_name)
            guild_map[g_name] = g_id
        
        self._discord_guild_map = guild_map
        self._discord_guild_items = items
        
        if dpg.does_item_exist("discord_ping_server"):
            dpg.configure_item("discord_ping_server", items=items)
            
            saved_id = getattr(self, "discord_ping_server", "")
            current = ""
            for display, gid in guild_map.items():
                if str(gid) == saved_id:
                    current = display
                    break
            dpg.set_value("discord_ping_server", current)
            if current:
                self._fetch_discord_roles(str(guild_map[current]))
                self._fetch_discord_channels_for_guild(str(guild_map[current]))

    def _fetch_discord_roles(self, guild_id_str: str):
        if not guild_id_str or not guild_id_str.isdigit():
            return
        if not self._discord_service.is_running:
            return
        guild_id = int(guild_id_str)
        self._discord_service.get_roles(
            guild_id=guild_id,
            on_result=lambda roles: self._queue_on_main(
                lambda: self._on_roles_fetched(roles)),
            on_error=lambda e: self._set_discord_status(f"Error fetching roles: {e}")
        )

    def _on_roles_fetched(self, roles: list[tuple[str, int]]):
        items = ["None"]
        role_map = {"None": ""}
        for r_name, r_id in roles:
            display = f"@{r_name}"
            items.append(display)
            role_map[display] = r_id
            
        self._discord_role_map = role_map
        self._discord_role_items = items
        
        if dpg.does_item_exist("discord_ping_roles"):
            dpg.configure_item("discord_ping_roles", items=items)
            
            saved_id = getattr(self, "discord_ping_roles", "")
            current = "None"
            for display, rid in role_map.items():
                if str(rid) == saved_id:
                    current = display
                    break
            dpg.set_value("discord_ping_roles", current)

    def _save_bot_token(self):
        """Persist the bot token from the input field."""
        if dpg.does_item_exist("discord_bot_token"):
            self.discord_bot_token = dpg.get_value("discord_bot_token").strip()
            self.save_settings()

    def _set_discord_status(self, text: str):
        """Update the Discord status label (thread-safe via work queue)."""
        def _update():
            if dpg.does_item_exist("discord_status_text"):
                dpg.set_value("discord_status_text", f"  {text}")
            # Auto-fetch guilds when connected
            if "connected" in text.lower() or "ready" in text.lower():
                self._fetch_discord_guilds()
                show_toast(text, severity="success", duration=3.0)
            elif "error" in text.lower() or "failed" in text.lower():
                show_toast(text, severity="error", duration=5.0)
            elif "posted" in text.lower():
                show_toast(text, severity="success", duration=4.0)
            elif "disconnect" in text.lower():
                show_toast(text, severity="warning", duration=3.0)
        self._queue_on_main(_update)

    def _connect_discord_bot(self):
        """Start the Discord bot with the saved token."""
        token = getattr(self, "discord_bot_token", "")
        if dpg.does_item_exist("discord_bot_token"):
            token = dpg.get_value("discord_bot_token").strip()
            self.discord_bot_token = token
            self.save_settings()
        if not token:
            self._set_discord_status("No bot token provided.")
            return
        self._set_discord_status("Connecting...")
        self._discord_service.start(token, on_status=self._set_discord_status)

    def _disconnect_discord_bot(self):
        """Stop the Discord bot."""
        self._discord_service.stop()

    def _confirm_post_to_discord(self):
        """Show confirmation before posting."""
        ch_display = ""
        if dpg.does_item_exist("discord_channel"):
            ch_display = dpg.get_value("discord_channel") or "selected channel"
        confirm(
            f"Post lineup to {ch_display}?",
            on_confirm=self._post_to_discord,
            title="Post to Discord",
            confirm_label="Post",
        )

    def _post_to_discord(self):
        """Post the current lineup as a Discord embed to the selected channel."""
        import datetime as _dt
        import discord

        if not self._discord_service.is_running:
            self._set_discord_status("Bot is not connected.")
            return

        channel_id_str = getattr(self, "discord_channel_id", "").strip()
        if not channel_id_str:
            self._set_discord_status("No channel selected.")
            return
        try:
            channel_id = int(channel_id_str)
        except ValueError:
            self._set_discord_status("Invalid channel ID.")
            return

        snap = self._build_snapshot()
        if not snap.slots:
            self._set_discord_status("Lineup is empty — nothing to post.")
            return

        body_text = dpg.get_value("output_text") if dpg.does_item_exist("output_text") else ""
        if not body_text.strip():
            self._set_discord_status("Output is empty.")
            return

        image_path = getattr(self, "discord_embed_image", "").strip()
        attach_file = None

        ping_roles = getattr(self, "discord_ping_roles", "").strip()
        ping_content = " ".join([f"<@&{r.strip()}>" for r in ping_roles.split(",") if r.strip()]) if ping_roles else ""

        embed_desc = body_text
        if ping_content:
            embed_desc = f"{body_text}\n\n{ping_content}".strip()

        embed = discord.Embed(
            description=embed_desc,
            color=0x4F46E5,
        )

        if image_path:
            if image_path.startswith(("http://", "https://")):
                embed.set_image(url=image_path)
            elif _os.path.isfile(image_path):
                ext = _os.path.splitext(image_path)[1]
                safe_name = f"image{ext}"
                attach_file = discord.File(image_path, filename=safe_name)
                embed.set_image(url=f"attachment://{safe_name}")

        ch_display = ""
        if dpg.does_item_exist("discord_channel"):
            ch_display = dpg.get_value("discord_channel") or "channel"

        self._set_discord_status(f"Posting to {ch_display}...")
        self._discord_service.send_embed(
            channel_id,
            embed=embed,
            content=None,
            file=attach_file,
            on_success=lambda: self._set_discord_status(
                f"Posted to {ch_display}."),
            on_error=lambda e: self._set_discord_status(f"Error: {e}"),
        )