"""
Discord OAuth2 helper — no GUI imports.
Opens the user's browser for Discord OAuth2 authorization,
catches the redirect on a temporary local HTTP server,
exchanges the code for an access token, and fetches basic user info.
"""

import http.server
import json
import secrets
import threading
import urllib.error
import urllib.parse
import urllib.request
from typing import Callable

DISCORD_AUTH_URL = "https://discord.com/api/oauth2/authorize"
DISCORD_TOKEN_URL = "https://discord.com/api/oauth2/token"
DISCORD_USER_URL = "https://discord.com/api/users/@me"
SCOPES = "identify guilds"
OAUTH_PORT = 18457
REDIRECT_URI = f"http://127.0.0.1:{OAUTH_PORT}/callback"
USER_AGENT = "LineupBuilder/1.0 (Desktop App)"


class DiscordOAuth:
    """Manages Discord OAuth2 sign-in for a desktop app."""

    def __init__(self):
        self.access_token: str = ""
        self.user_info: dict | None = None  # {"id", "username", "discriminator", "avatar"}

    @property
    def is_signed_in(self) -> bool:
        return bool(self.access_token and self.user_info)

    @property
    def display_name(self) -> str:
        if not self.user_info:
            return ""
        name = self.user_info.get("global_name") or self.user_info.get("username", "")
        return name

    def restore(self, data: dict):
        """Restore saved OAuth state from settings."""
        self.access_token = data.get("access_token", "")
        self.user_info = data.get("user_info")
        # Validate the token is still good
        if self.access_token:
            try:
                self.user_info = self._fetch_user(self.access_token)
            except Exception:
                self.access_token = ""
                self.user_info = None

    def to_dict(self) -> dict:
        """Serialize state for settings persistence."""
        return {
            "access_token": self.access_token,
            "user_info": self.user_info,
        }

    def sign_out(self):
        self.access_token = ""
        self.user_info = None

    def start_sign_in(
        self,
        client_id: str,
        client_secret: str,
        *,
        on_success: Callable[[dict], None] | None = None,
        on_error: Callable[[str], None] | None = None,
    ):
        """Open browser for OAuth2 and handle the redirect in a background thread."""
        if not client_id.strip():
            if on_error:
                on_error("No Client ID configured.")
            return

        thread = threading.Thread(
            target=self._run_flow,
            args=(client_id.strip(), client_secret.strip(), on_success, on_error),
            daemon=True,
        )
        thread.start()

    # ── Internal ──────────────────────────────────────────────────────────

    def _run_flow(self, client_id, client_secret, on_success, on_error):
        state = secrets.token_urlsafe(16)

        # Build authorize URL
        params = {
            "client_id": client_id,
            "redirect_uri": REDIRECT_URI,
            "response_type": "code",
            "scope": SCOPES,
            "state": state,
        }
        auth_url = f"{DISCORD_AUTH_URL}?{urllib.parse.urlencode(params)}"

        # Open browser
        import webbrowser
        webbrowser.open(auth_url)

        # Wait for redirect
        result = {"code": None, "error": None}

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                parsed = urllib.parse.urlparse(self.path)
                qs = urllib.parse.parse_qs(parsed.query)
                if parsed.path == "/callback":
                    got_state = qs.get("state", [None])[0]
                    if got_state != state:
                        result["error"] = "State mismatch — possible CSRF."
                    elif "error" in qs:
                        result["error"] = qs["error"][0]
                    else:
                        result["code"] = qs.get("code", [None])[0]

                    self.send_response(200)
                    self.send_header("Content-Type", "text/html")
                    self.end_headers()
                    msg = "Sign-in successful! You can close this tab."
                    if result["error"]:
                        msg = f"Sign-in failed: {result['error']}"
                    self.wfile.write(
                        f"<html><body><h2>{msg}</h2></body></html>".encode()
                    )
                else:
                    self.send_response(404)
                    self.end_headers()

            def log_message(self, *args):
                pass  # silence request logs

        try:
            server = http.server.HTTPServer(("127.0.0.1", OAUTH_PORT), Handler)
        except OSError as exc:
            if on_error:
                on_error(f"Could not start local server on port {OAUTH_PORT}: {exc}")
            return
        server.timeout = 120  # 2 minute timeout
        server.handle_request()
        server.server_close()

        if result["error"]:
            if on_error:
                on_error(result["error"])
            return

        code = result["code"]
        if not code:
            if on_error:
                on_error("No authorization code received.")
            return

        # Exchange code for token
        try:
            token_data = self._exchange_code(client_id, client_secret, code, REDIRECT_URI)
            self.access_token = token_data["access_token"]
            self.user_info = self._fetch_user(self.access_token)
            if on_success:
                on_success(self.user_info)
        except Exception as exc:
            if on_error:
                on_error(str(exc))

    def _exchange_code(self, client_id, client_secret, code, redirect_uri) -> dict:
        data = urllib.parse.urlencode({
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
        }).encode()
        req = urllib.request.Request(
            DISCORD_TOKEN_URL, data=data,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": USER_AGENT,
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as exc:
            body = exc.read().decode(errors="replace")
            # Try to parse Discord's JSON error for a readable message
            detail = body
            try:
                err = json.loads(body)
                desc = err.get("error_description") or err.get("message") or ""
                code_val = err.get("error") or err.get("code") or ""
                detail = f"{code_val}: {desc}".strip(": ") if (code_val or desc) else body
            except (json.JSONDecodeError, AttributeError):
                pass
            hint = ""
            if exc.code == 403:
                hint = (
                    f"\nCheck Discord Developer Portal → OAuth2 → Redirects "
                    f"includes exactly: {redirect_uri}"
                    f"\nAlso verify your Client Secret is current."
                )
            raise RuntimeError(
                f"Discord OAuth failed ({exc.code}): {detail}{hint}"
            ) from exc

    @staticmethod
    def _fetch_user(access_token: str) -> dict:
        req = urllib.request.Request(
            DISCORD_USER_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "User-Agent": USER_AGENT,
            },
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
