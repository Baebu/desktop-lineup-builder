import logging
import dearpygui.dearpygui as dpg

from ..styling.fonts import styled_text, MUTED, ERROR
from .widgets import add_primary_button

log = logging.getLogger("ui-builder-auth")

class AuthBuilderMixin:
    def _apply_local_mode_visibility(self):
        """Hide server-dependent tabs/sections when running in local mode."""
        is_local = getattr(self, "_local_mode", False)
        for tag in ("DJ", "DiscordTab", "sect_club_vrchat", "sect_roster_booked"):
            if dpg.does_item_exist(tag):
                dpg.configure_item(tag, show=not is_local)
        self._update_auth_card()

    def _update_auth_card(self):
        """Refresh the auth card button label to reflect sign-in state."""
        if not dpg.does_item_exist("auth_card_btn"):
            return
        _pad = "      "  # space for avatar overlay
        if self._oauth.is_signed_in:
            user = self._oauth.user_info or {}
            name = user.get("username", "Unknown")
            dpg.configure_item("auth_card_btn", label=f"{_pad}{name}")
        else:
            dpg.configure_item("auth_card_btn", label=f"{_pad}Local")
        self._position_auth_avatar()

    def _position_auth_avatar(self):
        """Place the avatar image on top of the auth card button."""
        if not dpg.does_item_exist("auth_card_btn") or not dpg.does_item_exist("auth_card_avatar"):
            return
        btn_pos = dpg.get_item_pos("auth_card_btn")
        btn_h = dpg.get_item_height("auth_card_btn")
        av_sz = 24
        x = btn_pos[0] + 8
        y = btn_pos[1] + max(0, (btn_h - av_sz) // 2)
        dpg.configure_item("auth_card_avatar", pos=[x, y], show=True)

    def _load_discord_avatar(self, user: dict):
        """Download and display the user's Discord avatar in the auth card."""
        user_id = user.get("id", "")
        avatar_hash = user.get("avatar", "")
        if not user_id or not avatar_hash:
            return

        url = f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.png?size=32"

        def _fetch():
            try:
                import urllib.request
                import io
                from PIL import Image

                req = urllib.request.Request(url, headers={"User-Agent": "LineupBuilder/1.2"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = resp.read()
                img = Image.open(io.BytesIO(data)).convert("RGBA").resize((32, 32))
                # Normalise to 0–1 floats for DPG
                pixels =[v / 255.0 for v in img.tobytes()]

                def _apply():
                    if dpg.does_item_exist("auth_avatar_tex"):
                        dpg.delete_item("auth_avatar_tex")
                    if dpg.does_alias_exist("auth_avatar_tex"):
                        dpg.remove_alias("auth_avatar_tex")
                    # Target the global registry instead of creating an anonymous one
                    dpg.add_static_texture(32, 32, pixels, tag="auth_avatar_tex", parent="global_texture_registry")
                    
                    if dpg.does_item_exist("auth_avatar_img"):
                        dpg.configure_item("auth_avatar_img", texture_tag="auth_avatar_tex", show=True)
                    if dpg.does_item_exist("auth_card_avatar"):
                        dpg.configure_item("auth_card_avatar", texture_tag="auth_avatar_tex")
                self._work_queue.put(_apply)
            except Exception as exc:
                log.debug("Failed to load Discord avatar: %s", exc)

        import threading
        threading.Thread(target=_fetch, daemon=True).start()

    def _build_account_drawer(self):
        """Build the account drawer contents (created once, shown/hidden)."""
        dpg.add_spacer(height=4)

        # Avatar + status row
        with dpg.group(horizontal=True):
            dpg.add_image(
                "auth_avatar_tex", tag="account_avatar_img",
                width=32, height=32, show=False,
            )
            styled_text("  Not signed in", MUTED, tag="account_status_text")
        dpg.add_spacer(height=6)

        # Sign-in button
        add_primary_button(
            "Sign in with Discord",
            tag="account_signin_btn",
            width=-1,
            callback=lambda: self._sign_in_from_app(),
        )

        # Sign-out button (hidden when not signed in)
        from .widgets import add_danger_button
        add_danger_button(
            "Sign Out",
            tag="account_signout_btn",
            width=-1,
            callback=lambda: self._sign_out_from_drawer(),
        )

        # Local-mode toggle
        dpg.add_checkbox(
            tag="account_local_mode_cb",
            label="Local Mode",
            default_value=getattr(self, "_local_mode", False),
            callback=lambda s, a: self._toggle_local_mode_from_drawer(a),
        )
        dpg.add_spacer(height=2)
        styled_text("", ERROR, tag="account_error_label")

    def _toggle_account_drawer(self):
        """Toggle the account drawer open/closed."""
        self._account_drawer_open = not self._account_drawer_open
        show = self._account_drawer_open
        dpg.configure_item("account_drawer", show=show)
        # Shrink tabs wrapper to make room for the drawer
        offset = self._AUTH_BTN_HEIGHT + (self._DRAWER_HEIGHT if show else 0)
        dpg.configure_item("left_tabs_wrapper", height=-offset)
        if show:
            self._refresh_account_drawer()
        # Reposition avatar overlay after layout shift
        self._work_queue.put(self._position_auth_avatar)

    def _sign_out_from_drawer(self):
        """Sign out and update the drawer + auth card."""
        self._local_mode = True
        self._oauth.sign_out()
        self.discord_oauth = {}
        self.save_settings()
        self._apply_local_mode_visibility()
        self._refresh_account_drawer()

    def _toggle_local_mode_from_drawer(self, value):
        """Toggle local mode from the drawer checkbox."""
        self._local_mode = bool(value)
        self._apply_local_mode_visibility()
        self._refresh_account_drawer()

    def _refresh_account_drawer(self):
        """Update the account drawer to reflect current sign-in status."""
        if not dpg.does_item_exist("account_status_text"):
            return
        signed_in = self._oauth.is_signed_in
        if signed_in:
            user = self._oauth.user_info or {}
            name = user.get("username", "Unknown")
            dpg.set_value("account_status_text", f"  Signed in as {name}")
            dpg.configure_item("account_signin_btn", show=False)
            dpg.configure_item("account_signout_btn", show=True)
            dpg.configure_item("account_local_mode_cb", show=False)
            dpg.set_value("account_error_label", "")
            if dpg.does_item_exist("account_avatar_img"):
                dpg.configure_item("account_avatar_img", show=True)
            self._load_discord_avatar(user)
        else:
            dpg.set_value("account_status_text", "  Not signed in")
            dpg.configure_item("account_signin_btn", show=True)
            dpg.configure_item("account_signout_btn", show=False)
            dpg.configure_item("account_local_mode_cb", show=True)
            if dpg.does_item_exist("account_avatar_img"):
                dpg.configure_item("account_avatar_img", show=False)
        self._update_auth_card()