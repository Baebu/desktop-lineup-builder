# Lineup Builder — Desktop App

A **DearPyGui**-based desktop application for DJs and event organizers to create, manage, and share event lineups. Streamlines scheduling performer sets, managing rosters, and generating formatted output for Discord, plain text, and VRCDN-based VR platforms (Quest/PC).

Built with a **mixin-composition architecture**: the entire backend is pure Python with zero GUI dependencies — fully unit-testable and reusable by web/server clients.

## Features at a Glance

| Category | Capability |
|----------|-----------|
| **Lineup Creation** | Smart event header (title, vol #), date/time picker, auto-import from Discord/text, drag-to-reorder slots, genre tagging |
| **DJ Roster** | Persistent roster with stream links (VRCDN, Twitch, YouTube, etc.), exact-link mode, drag-and-drop into slots |
| **Output Formats** | Real-time text preview, rich visual Discord embed mockup, Local (plain text), Quest (HLS links), PC (RTSP links) |
| **Discord Bot** | Post lineups as rich embeds with auto-computed times, schedule posts for future delivery, image attachment |
| **Cloud Sync** | Sign in via Discord OAuth2 to automatically sync your library and events to the cloud, or remain in Local Mode |
| **Themes** | 8 built-in presets + unlimited custom presets, Windows title bar coloring (Win10/11), persistent preferences |
| **Reliability** | Auto-save every 5 sec, crash recovery, window/panel geometry persistence, single-file SQLite database storage |

---

## Screenshots

![Screenshot 1](../assets/Screenshots/Screenshot%202026-03-07%20025936.png)
![Screenshot 2](../assets/Screenshots/Screenshot%202026-03-07%20025953.png)
![Screenshot 3](../assets/Screenshots/Screenshot%202026-03-07%20030001.png)
![Screenshot 4](../assets/Screenshots/Screenshot%202026-03-07%20030012.png)

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **GUI Framework** | DearPyGui 1.11+ | Immediate-mode vector renderer, low-level widget control |
| **Discord Integration** | discord.py 2.3+ | Bot client for posting, OAuth2 for user login |
| **Data Storage** | SQLite3 (Built-in) | Single-file local database (`lineup_builder.db`) |
| **Image Processing** | Pillow 10+ | Load images for embed attachments and UI avatars |
| **File Watching** | watchdog 3.0+ | Auto-restart dev server on code changes |
| **HTTP Client** | urllib (built-in) | REST calls for OAuth2 and Cloud Sync |

---

## Architecture Overview

### Mixin-Composition Design

The `App` class multiply inherits **13 functional mixins**, each responsible for a distinct feature area:

| # | Mixin | File | Responsibility |
|---|-------|------|---|
| 1 | `UISetupMixin` | `ui/init.py` | DPG viewport, left/right panels, tabs, all widget construction |
| 2 | `RosterMixin` | `mixins/roster.py` | DJ roster CRUD, bulk link import, drag payload creation |
| 3 | `DragDropMixin` | `mixins/drag_drop.py` | Slot reordering, DJ-card→slot drop targets, flash highlight |
| 4 | `EventsMixin` | `mixins/events_manager.py` | Save/load/delete/duplicate event lineups |
| 5 | `GenreMixin` | `mixins/genre_manager.py` | Genre tag add/delete/toggle, active-genre filtering |
| 6 | `SlotMixin` | `mixins/slot_manager.py` | Slot CRUD, reorder, apply master duration |
| 7 | `OutputMixin` | `backend/output/output_builder.py` | `_build_snapshot()` → `EventSnapshot`; `update_output()` drives preview |
| 8 | `DataMixin` | `backend/data_manager.py` | SQLite I/O, cloud sync, window geometry persistence |
| 9 | `SettingsMixin` | `mixins/settings_manager.py` | `load_settings()`, `apply_theme()`, preset management |
| 10 | `SectionsMixin` | `mixins/sections.py` | Collapsible UI section management for left-panel tabs |
| 11 | `DebounceMixin` | `backend/debounce.py` | Timer helpers + per-frame work queue (`process_queue()`) |
| 12 | `ImportMixin` | `mixins/import_parser.py` | `_parse_event_text()` for Discord markdown and plain-text formats |
| 13 | `KeyboardMixin` | `mixins/keyboard_handler.py` | Global keyboard shortcuts (Ctrl+S, Ctrl+N, etc.) |

**Golden rule:** `src/backend/` is **100% GUI-free**. No DearPyGui imports. Tests run against backend only.

### Layer Separation

| Layer | Location | Constraint |
|-------|----------|-----------|
| **Backend** | `src/backend/` | Pure Python — no DearPyGui, no UI dependencies |
| **Frontend** | `src/frontend/` | DearPyGui widgets, themes, fonts, UI only |
| **Tests** | `tests/` | pytest against backend (no GUI testing) |

---

## Directory Structure

```
desktop/
├── main.py                          # Entry point + AppUserModelID for Windows
├── dev.py                           # Auto-restart dev runner (watchdog)
├── dev.bat                          # Batch shortcut for dev.py
├── requirements.txt                 # Python dependencies
├── lineup_builder.spec              # PyInstaller spec for .exe build
│
├── src/
│   └── frontend/                    # DearPyGui GUI — ALL widget code
│       ├── app.py                   # App class: mixin composition + DPG lifecycle
│       ├── types.py                 # TypeVar, generic types used across frontend
│       ├── utils.py                 # get_data_dir(), get_icon_path()
│       │
│       ├── mixins/                  # 13 functional mixins (see table above)
│       │   ├── drag_drop.py         # Drag-and-drop slot reorder, DJ drop targets
│       │   ├── events_manager.py    # Save/load/delete/duplicate event lineups
│       │   ├── genre_manager.py     # Genre CRUD, filtering, tag management
│       │   ├── import_parser.py     # Parse Discord/plain-text event imports
│       │   ├── keyboard_handler.py  # Global keyboard shortcuts
│       │   ├── roster.py            # DJ roster sidebar, CRUD, link import
│       │   ├── sections.py          # Persistent sections (top panel, etc.)
│       │   ├── settings_manager.py  # Theme selection, preset save/load
│       │   ├── slot_manager.py      # Slot UI rendering, add/delete/reorder
│       │   └── __init__.py
│       │
│       ├── styling/                 # Theming & typography
│       │   ├── theme.py             # 50+ color token hex strings, style dicts
│       │   ├── fonts.py             # Material Symbols Icon class, styled_text()
│       │   └── __init__.py
│       │
│       └── ui/                      # Low-level widget builders
│           ├── builder/             # Layout builders (panels, tabs, grid)
│           ├── auth.py              # Discord OAuth UI
│           ├── confirm_dialog.py    # Reusable confirmation modal
│           ├── date_time_picker.py  # Calendar + time picker modal
│           ├── discord.py           # Discord bot connection, channel picker
│           ├── discord_schedule.py  # Pending and scheduled post interfaces
│           ├── init.py              # UISetupMixin: full window/panel layout
│           ├── interactions.py      # Right-click menus, context handling
│           ├── layout.py            # Panel manager, flex layouts
│           ├── preview.py           # Visual output preview panel (Discord mock)
│           ├── slot_ui.py           # DPGVar, DPGBoolVar, SlotState, slot row builder
│           ├── tabs.py              # Tab switching, rendering
│           ├── toast.py             # Toast notification helper
│           ├── widgets.py           # Themed widget factory (buttons, inputs, etc.)
│           └── __init__.py
│
│   └── backend/                     # Pure Python — ZERO DearPyGui imports
│       ├── database.py              # Database: Single-file SQLite storage
│       ├── data_manager.py          # DataMixin: SQLite I/O and Cloud Sync
│       ├── debounce.py              # DebounceMixin: timers + frame work queue
│       │
│       ├── models/
│       │   ├── event_bus.py         # EventBus: pub/sub for cross-module events
│       │   ├── lineup_model.py      # LineupModel + SlotData / DJInfo dataclasses
│       │   ├── types.py             # EventSnapshot, shared type hints
│       │   └── __init__.py
│       │
│       ├── output/
│       │   ├── output_builder.py    # OutputMixin: UI state → EventSnapshot
│       │   ├── output_generator.py  # Pure stateless text generation
│       │   └── __init__.py
│       │
│       ├── services/
│       │   ├── discord_oauth.py     # OAuth2 local server callback
│       │   ├── discord_service.py   # DiscordService: bot lifecycle + posting
│       │   └── __init__.py
│       │
│       └── __init__.py
│
├── build/                           # PyInstaller build artifacts (gitignored)
├── dist/                            # dist/LineupBuilder.exe (gitignored)
│
├── lineup_builder.db                # SQLite database containing ALL user data
│
└── README.md (this file)
```

---

## Features in Detail

### Authentication & Cloud Sync

**Local vs. Cloud Mode**
- By default, the app runs in **Local Mode**, securely saving all library and event data to your local SQLite database.
- Connect your Discord account via the integrated OAuth2 login to unlock **Cloud Sync**.
- In Cloud Mode, your DJ library, genres, and saved events automatically sync to the backend API, enabling multi-device access and server-side persistence.

### Event Creation & Orchestration

**Smart Header**
- Set event title and volume number
- Volume auto-increments when duplicating a saved event
- Persistent favorite titles for quick access

**Date & Time Picker**
- Custom-styled modal calendar (click date to select)
- Time input with up/down arrow shortcuts:
  - **↑ / ↓** → shift ±15 minutes
  - **Shift + ↑ / ↓** → shift ±24 hours
- Real-time preview of Unix timestamp

**Automated Import**
- Paste existing lineup from Discord markdown or plain text
- Parser extracts: title, timestamp, genres, DJ names and durations
- Review parsed data before confirming
- Handles various Discord formatting styles

**Genre Library**
- Global persistent genre list (shared across all events)
- Toggle genres on/off per event for smart filtering
- Add new genres on-the-fly; auto-saved to SQLite/Cloud
- Genre tags appear in output and Discord embeds

### DJ Roster & Lineup Management

**Persistent Roster**
- Add/edit/delete DJs with name, stream link, genre tags
- Stream links: support VRCDN (auto-convert between Quest/PC), Twitch, YouTube, SoundCloud, Kick, custom URLs
- **Exact Link Mode** — per-DJ toggle to skip VRCDN conversion and pass URL as-is
- Bulk link import from formatted text

**Drag-and-Drop Slots**
- Drag DJ from roster directly into a lineup slot
- Visual feedback: highlight drop zone, ghost clone while dragging
- Drag slot handles to reorder (auto-compute new times)
- Slot auto-deletion when dragging to trash

**Slot Management**
- Duration presets: 15 to 120 minutes (configurable)
- Apply master duration to all open slots at once
- Real-time time label computation (HH:MM based on event start + cumulative durations)
- Fast autocomplete search field for instantly typing a DJ's name
- Support for "Open Deck" placeholder slots

**Events History**
- Save current lineup with a name (persisted to SQLite/Cloud)
- Load past event → restores all slots and settings
- Duplicate event → copy with new name, auto-increments the volume, shifts date exactly 1 week ahead
- Delete event → permanent removal with confirmation
- Events sortable by date

### Discord Bot Integration

**Bot Connection**
- Connect your own custom Discord bot directly from the app
- Display current bot status and auto-reconnect on disconnect
- Embedded token refresh UI
- **Note:** Ensure **Message Content Intent** is enabled for your bot in the Discord Developer Portal.

**Rich Embed Posting**
- Post lineups immediately as Discord embeds
- Embed includes: event title + volume, timestamp (Discord `<t:UNIX:F>` format), genres, full slot lineup with times
- DJ names bold, genre badges, computed slot times with timezone
- Embed color matches active theme accent
- Optional embed image (from URL or local file)
- Integrated role ping drop-down menu

**Channel Picker**
- Dropdown list of your Discord server's text channels
- Bot must have `67584` permissions (Send Messages, Embed Links) in selected channel
- Channel validation before posting

**Scheduled Posting**
- Schedule posts for future delivery (specify date/time)
- Posts persist in your settings across app restarts
- Background scheduler checks periodically and fires due posts
- **Important Note:** The Lineup Builder application **must be running** at the scheduled time for the post to be delivered!

### Social Links

**Configurable Social Platforms**
- Support for: Timeline, VRCPop, X (Twitter), Instagram, Discord, VRC Group
- Add/edit/remove links per event
- Links appear formatted at bottom of output and Discord embeds
- **Persistent Links** — toggle to auto-carry Discord & VRC Group links across all events automatically

### Multi-Format Output

Real-time previews for all output formats:

| Format | Style | Link Conversion | Use Case |
|--------|-------|---|---|
| **Visual** | Rich UI Mockup | N/A | Accurate visual preview of the Discord Markdown formatting and attached image |
| **Discord** | Markdown embeds | None (pass-through) | Posting to Discord |
| **Local** | Plain text, HH:MM times | None (pass-through) | Local printing, archives |
| **Quest** | HLS m3u8 links | VRCDN → `https://stream.vrcdn.live/live/{key}.live.ts` | VRChat Quest clients |
| **PC** | RTSP links | VRCDN → `rtspt://stream.vrcdn.live/live/{key}` | VRChat PC clients |

### Personalization & Reliability

**Theme Engine**
- 8 built-in dark presets: Slate (default), Midnight Blue, OLED Black, Crimson, Amber, Forest, Ocean, Violet
- Full customization: 30+ color tokens (panel bg, text, buttons, etc.)
- Save custom themes as named presets
- Windows title bar coloring — matches theme on Windows 10/11
- Applies globally to all popups and dialogs

**Crash Recovery**
- Auto-save every 5 seconds to internal state memory
- On app launch, detect previous crash and offer recovery
- Save recovers full event state (all slots, settings, text inputs) and restores to editor

**Window & Panel Persistence**
- Remembers window size, position between sessions
- Remembers left/right panel split position (drag handle)
- Auto-layout responsive to small windows (800×600 minimum)

---

## Input Shortcuts & Tips

| Input | Action |
|-------|--------|
| **Ctrl + S** | Save current event lineup |
| **Ctrl + N** | Start a new event lineup |
| **↑ / ↓** on timestamp field | Shift event time ±15 minutes |
| **Shift + ↑ / ↓** on timestamp field | Shift event time ±24 hours |
| **Mouse wheel** on combo / duration spinners | Cycle values up or down |
| **Right-click** on any input | Copy/paste context menu (auto-added) |
| **Drag slot handle** | Reorder slots; times auto-compute |
| **Drag DJ card→slot** | Add DJ to slot with confirmation |
| **Type in Slot Name** | Auto-complete filters matching roster DJs |

---

## Getting Started

### Prerequisites

- **Python 3.11+**
- **Windows 10/11** (optional — native title bar coloring; app runs on macOS/Linux without it)
- **Discord bot token** (optional — for Discord posting; get from [Developer Portal](https://discord.com/developers/applications))

### Installation

```bash
cd desktop
python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows PowerShell
# or: source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

### Configuration via `.env` (Optional)

You can pre-populate your Discord credentials by placing a `.env` file in the application's runtime data directory (the root of the repo during development, or next to the executable if compiled):

```ini
DISCORD_BOT_TOKEN=your_bot_token_here
DISCORD_CLIENT_ID=your_client_id_here
```

### Run

```bash
# Production build (from desktop/)
python main.py

# Development with auto-restart on code changes (watchdog)
python dev.py
# or: dev.bat (Windows batch shortcut)

# From project root (if desired)
cd ..
python desktop/main.py
```

### Build Standalone Executable

```bash
pip install pyinstaller
cd desktop
python -m PyInstaller lineup_builder.spec --clean
```

Output: `dist/LineupBuilder.exe` (Windows) or `dist/LineupBuilder` (macOS/Linux)

### Test Backend

```bash
# Run pytest against pure backend (no GUI testing)
pytest tests/ -v

# Test specific module
pytest tests/test_output_generator.py -v

# Run with coverage
pytest tests/ --cov=src/backend/ --cov-report=html
```

---

## Data Files

All application data is securely stored in a single SQLite database file (`lineup_builder.db`) located in the application directory (resolved by `get_data_dir()`):
- **During development:** Project root (`desktop/`)
- **After PyInstaller build:** Executable's directory

### Legacy Migration
If you are upgrading from an older version of Lineup Builder, the app will automatically detect your old `.yaml` and `.json` files on launch, securely migrate all your data into the new SQLite database, and rename the old files to `*.migrated` to prevent conflicts.

---

## State Flow & Event Bus

The app uses a **reactive event-driven** pattern:

```
User interacts with UI widget
  ↓
DPGVar/DPGBoolVar wrapper captures value
  ↓
Mixin callback fires (e.g., SlotMixin.on_slot_name_changed())
  ↓
Model setter: model.set_slot_name(id, value)
  ↓
Model state mutates
  ↓
Model publishes 'model_changed' on EventBus
  ↓
OutputMixin (subscribed) wakes up
  ↓
_build_snapshot() → EventSnapshot (immutable)
  ↓
OutputGenerator.generate(snap) → formatted string
  ↓
dpg.set_value(preview_tag, new_text)
  ↓
User sees updated preview
```

**Cross-module communication** via `EventBus` pub/sub in `src/backend/models/event_bus.py`:
- `subscribe(event, callback)` — Register a handler
- `publish(event, data)` — Broadcast to all subscribers
- No coupling between modules; all go through the bus

---

## Debounce & Performance

Heavy operations are debounced to prevent UI lag:

| Method | Delay | Purpose |
|--------|-------|---------|
| `_schedule_update()` | 150 ms | Refresh output preview. Coalesces rapid model changes. |
| `_schedule_roster_refresh()` | 120 ms | Redraw DJ roster panel after bulk import or genre filter. |
| `_schedule_genre_refresh()` | 120 ms | Redraw genre tag list after add/delete. |
| `_schedule_save_library()` | 500 ms | Persist DJ/genre library to SQLite/Cloud. Avoids thrashing DB/API. |
| `_schedule_auto_save()` | 5000 ms | Write crash-recovery state to key-value storage. |

All timer work goes through `DebounceMixin` and a work queue (`self._work_queue`). The main loop calls `process_queue()` each frame to drain pending work on the UI thread.

---

## Code Architecture Guide

### Backend Modules (Pure Python, 100% GUI-free)

**models/event_bus.py**
- Simple pub/sub: `subscribe()`, `unsubscribe()`, `publish()`
- Core to cross-module communication

**models/lineup_model.py**
- `LineupModel` — mutable runtime state with change notification
- `SlotData`, `DJInfo` — plain dataclasses
- `EventSnapshot` — immutable snapshot for output generation

**output/output_generator.py**
- Pure stateless functions: `generate(snapshot)`, `compute_slot_times(snapshot)`, `vrcdn_convert(link, fmt)`
- No side effects; fully testable

**output/output_builder.py**
- `OutputMixin` — bridges UI state to `EventSnapshot` and triggers `OutputGenerator`
- `_build_snapshot()` — capture current editor state
- `update_output()` — refresh preview panel

**database.py**
- `Database` — Single-file SQLite storage engine
- Thread-safe connection management and table initialization
- Handles automatic migration from legacy YAML/JSON files

**data_manager.py**
- `DataMixin` — Bridges the UI with the `Database`
- Handles local SQLite reads/writes and background cloud synchronization via threading

**debounce.py**
- `DebounceMixin` — timer helpers + work queue

**services/discord_service.py**
- `DiscordService` — bot lifecycle, embed posting
- Handle bot connection, token refresh, message sending
- Scheduled post tracking and firing

**services/discord_oauth.py**
- `DiscordOAuth` — OAuth2 local callback server
- User login flow, token caching, profile fetching

### Frontend Modules (DearPyGui widgets only)

**app.py**
- `App` class — inherits all 13 mixins
- Owns DPG lifecycle: create context → create viewport → setup → show → main loop

**ui/init.py (UISetupMixin)**
- `UISetupMixin` — Full window layout
- Create viewport, left/right panels, tabs, all widgets

**ui/slot_ui.py**
- `DPGVar`, `DPGBoolVar` — wrappers around `dpg.get_value()` / `dpg.set_value()`
- `SlotState` — per-slot state holder (name, genre, duration, row tag)
- `build_slot_row()` — single slot UI builder function

**mixins/***
- Each mixin handles a distinct feature (roster, slots, genres, events, drag-drop, etc.)
- Mixins are callback handlers for their UI sections

**styling/theme.py**
- 50+ hex color constants, semantic naming
- No hardcoded colors in widget code
- Reusable style dicts for unified aesthetics

**styling/fonts.py**
- Material Symbols icon mappings
- `styled_text()` helper for semantic typography

**ui/widgets.py**
- Themed widget factory functions
- `add_primary_button()`, `add_danger_button()`, `add_styled_combo()`, etc.

---

## Troubleshooting

### Issue: App won't start — "No module named dearpygui"
**Solution:** Ensure virtual environment is activated and `pip install -r requirements.txt` ran successfully. Try: `pip install dearpygui --upgrade`

### Issue: Discord bot won't connect / errors on posting
**Cause:** Invalid token, bot missing permissions, or Gateway Intents disabled.  
**Solution:** Verify your token in the [Discord Developer Portal](https://discord.com/developers/applications). Make sure your bot is invited with `67584` permissions (Send Messages, Embed Links). **Critically, ensure "Message Content Intent" is toggled ON in the Developer Portal.**

### Issue: Scheduled posts aren't appearing
**Cause:** The Lineup Builder app was closed.  
**Solution:** The internal scheduler runs on the application's clock. The app must remain open for the bot to post scheduled lineups. 

### Issue: Window too small, widgets cut off
**Cause:** Desktop too small or window minimized  
**Solution:** Resize window to at least 800×600. App auto-layouts for smaller sizes but 900×700 is recommended.

### Issue: Drag-drop not working
**Cause:** Slot row DOM structure incorrect  
**Solution:** Ensure `DragDropMixin.init()` was called during `App.__init__()`. Check that slot rows have correct tag `"slot_row_{id}"`.

### Issue: Theme doesn't apply to popups/modals
**Cause:** Popup created before theme bound  
**Solution:** All modals should be created *after* `apply_theme()` in `App.__init__()`. Global theme inheritance is automatic.

### Issue: Database locked error
**Cause:** Multiple instances of the app trying to write to `lineup_builder.db` simultaneously.  
**Solution:** Ensure only one instance of Lineup Builder is running at a time.

---

## Database Schema Reference

All data is stored in `lineup_builder.db` using the following core tables:

- **`kv`**: Key-Value store holding JSON blobs for `settings`, `window_state`, and `auto_save`.
- **`djs`**: DJ roster (`id`, `name`, `stream`, `exact_link`).
- **`genres`**: Global genre library.
- **`events`**: Saved event metadata (`title`, `vol`, `timestamp`, `social_links`, etc.).
- **`event_slots`**: Foreign-keyed to `events`, holding individual slot data (`position`, `name`, `genre`, `duration`).
- **`event_genres`**: Foreign-keyed to `events`, holding active genres for that specific event.

---

## Related Documentation

- **Web Client** — See [web/README.md](../web/README.md) for browser-based version
- **Server API** — See [server/README.md](../server/README.md) for REST backend
- **DearPyGui Docs** — https://dearpygui.readthedocs.io/
- **discord.py Docs** — https://discordpy.readthedocs.io/

## Build & Deployment

### PyInstaller Spec

The `lineup_builder.spec` file defines the executable build:
- Includes DearPyGui and all dependencies
- Bundles Material Symbols font
- Sets Windows icon and company name
- One-file build to `dist/LineupBuilder.exe`

### Distribution

Pre-built executables available on [GitHub Releases](https://github.com/Baebu/lineup_builder/releases).

## License

See [LICENSE](../LICENSE) at project root.

## Contributing

1. Create a feature branch: `git checkout -b feature/my-feature`
2. Make changes, test thoroughly: `pytest tests/ -v` and manual testing
3. Keep backend pure (no GUI imports)
4. Use debounce for heavy operations
5. Commit and push: `git push origin feature/my-feature`
6. Submit PR with description

---

**Last Updated:** 2026-03-16  
**Version:** 1.2.0
**Maintainer:** Baebu

## Theme System

Themes are defined as dictionaries of hex color tokens and applied by `SettingsMixin.apply_theme()`, which builds a global DPG theme covering 30+ color slots and rounded-corner styles.

### Built-in Presets

| Name | Description |
|------|-------------|
| **Slate** (Default) | Dark slate blue |
| **Midnight Blue** | Deep midnight blue with blue accents |
| **OLED Black** | Near-pure-black for OLED displays |
| **Crimson** | Deep red/rose tones |
| **Amber** | Warm amber/gold tones |
| **Forest** | Dark emerald green |
| **Ocean** | Deep teal/cyan |
| **Violet** | Rich purple |

### Color Tokens

`primary_color`, `primary_hover`, `secondary_color`, `secondary_hover`, `success_color`, `success_hover`, `danger_color`, `danger_hover`, `accent_color`, `panel_bg`, `card_bg`, `border_color`, `hover_color`, `scrollbar_color`, `text_primary`, `text_secondary`

---

## Output Formats

`OutputGenerator.generate(snapshot)` is a pure static method — no GUI, no side effects.
### Discord
```markdown
# Event Title VOL.3
# <t:1234567890:F> (<t:1234567890:R>)
## House // Techno
### LINEUP
<t:1234567890:t> | **DJ Alpha** (House)
<t:1234567950:t> | **DJ Beta** (Techno)
```

### Local (Plain Text)
```text
Event Title VOL.3
2025-06-01 @ 20:00 (PST)
House // Techno
LINEUP
20:00 | DJ Alpha (House)
20:30 | DJ Beta (Techno)
```

### Quest / PC (Stream Links)
```text
https://stream.vrcdn.live/live/{key}.live.ts   ← Quest (HLS)
rtspt://stream.vrcdn.live/live/{key}           ← PC (RTSP)
```