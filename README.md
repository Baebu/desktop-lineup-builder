# Lineup Builder — Desktop App

A **DearPyGui**-based desktop application for DJs and event organizers to create, manage, and share event lineups. Streamlines scheduling performer sets, managing rosters, and generating formatted output for Discord, plain text, and VRCDN-based VR platforms (Quest/PC).

Built with a **mixin-composition architecture**: the entire backend is pure Python with zero GUI dependencies — fully unit-testable and reusable by web/server clients.

## Features at a Glance

| Category | Capability |
|----------|-----------|
| **Lineup Creation** | Smart event header (title, vol #), date/time picker, auto-import from Discord/text, drag-to-reorder slots, genre tagging |
| **DJ Roster** | Persistent roster with stream links (VRCDN, Twitch, YouTube, etc.), exact-link mode, drag-and-drop into slots |
| **Output Formats** | Real-time preview: Discord (markdown embeds), Local (plain text), Quest (HLS links), PC (RTSP links) |
| **Discord Bot** | Post lineups as rich embeds with auto-computed times, schedule posts for future delivery, image attachment |
| **Themes** | 8 built-in presets + unlimited custom presets, Windows title bar coloring (Win10/11), persistent preferences |
| **Reliability** | Auto-save every 5 sec, crash recovery, window/panel geometry persistence, YAML-backed event/library storage |

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
| **Data Serialization** | PyYAML 6.0+ | Event/library YAML storage; JSON for settings |
| **Image Processing** | Pillow 10+ | Load images for embed attachments |
| **File Watching** | watchdog 3.0+ | Auto-restart dev server on code changes |
| **HTTP Client** | httpx (optional) | REST calls to backend API |

---

## Architecture Overview

### Mixin-Composition Design

The `App` class multiplies inherits **11 functional mixins**, each responsible for a distinct feature area:

| # | Mixin | File | Responsibility |
|---|-------|------|---|
| 1 | `UISetupMixin` | `ui/init.py` | DPG viewport, left/right panels, tabs, all widget construction, scroll/arrow-key handlers |
| 2 | `RosterMixin` | `mixins/roster.py` | DJ roster CRUD, bulk link import, drag payload creation |
| 3 | `DragDropMixin` | `mixins/drag_drop.py` | Slot reordering, DJ-card→slot drop targets, flash highlight |
| 4 | `EventsMixin` | `mixins/events_manager.py` | Save/load/delete/duplicate event lineups (YAML-backed) |
| 5 | `GenreMixin` | `mixins/genre_manager.py` | Genre tag add/delete/toggle, active-genre filtering |
| 6 | `SlotMixin` | `mixins/slot_manager.py` | Slot CRUD, reorder, apply master duration |
| 7 | `OutputMixin` | `backend/output/output_builder.py` | `_build_snapshot()` → `EventSnapshot`; `update_output()` drives preview |
| 8 | `DataMixin` | `backend/data_manager.py` | YAML/JSON I/O, window geometry persistence, crash-recovery auto-save |
| 9 | `SettingsMixin` | `mixins/settings_manager.py` | `load_settings()`, `apply_theme()`, preset management |
| 10 | `DebounceMixin` | `backend/debounce.py` | Timer helpers + per-frame work queue (`process_queue()`) |
| 11 | `ImportMixin` | `mixins/import_parser.py` | `_parse_event_text()` for Discord markdown and plain-text formats |

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
│       ├── mixins/                  # 11 functional mixins (see table above)
│       │   ├── drag_drop.py         # Drag-and-drop slot reorder, DJ drop targets
│       │   ├── events_manager.py    # Save/load/delete/duplicate event lineups
│       │   ├── genre_manager.py     # Genre CRUD, filtering, tag management
│       │   ├── import_parser.py     # Parse Discord/plain-text event imports
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
│           ├── init.py              # UISetupMixin: full window/panel layout
│           ├── interactions.py      # Right-click menus, context handling
│           ├── layout.py            # Panel manager, flex layouts
│           ├── preview.py           # Output preview panel
│           ├── slot_ui.py           # DPGVar, DPGBoolVar, SlotState, slot row builder
│           ├── tabs.py              # Tab switching, rendering
│           ├── toast.py             # Toast notification helper
│           ├── widgets.py           # Themed widget factory (buttons, inputs, etc.)
│           └── __init__.py
│
│   └── backend/                     # Pure Python — ZERO DearPyGui imports
│       ├── data_manager.py          # DataMixin: YAML/JSON file I/O
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
├── lineup_events.yaml               # Saved event lineups (user data)
├── lineup_library.yaml              # DJ roster + genre library (user data)
├── settings.json                    # Theme colors, UI prefs (user data)
├── window_state.json                # Window geometry, panel widths (user data)
├── auto_save.json                   # Crash-recovery transient state (user data)
│
└── README.md (this file)
```

---

## Features in Detail

### Event Creation & Orchestration

**Smart Header**
- Set event title and volume number
- Volume auto-increments when saving a new event
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
- Add new genres on-the-fly; auto-saved to YAML
- Genre tags appear in output and Discord embeds

### DJ Roster & Lineup Management

**Persistent Roster**
- Add/edit/delete DJs with name, stream link, genre tags
- Stream links: support VRCDN (auto-convert between Quest/PC), Twitch, YouTube, SoundCloud, Kick, custom URLs
- **Exact Link Mode** — per-DJ toggle to skip VRCDN conversion and pass URL as-is
- Bulk link import from formatted text
- Profile images load in roster cards

**Drag-and-Drop Slots**
- Drag DJ from roster directly into a lineup slot
- Visual feedback: highlight drop zone, ghost clone while dragging
- Drag slot handles to reorder (auto-compute new times)
- Slot auto-deletion when dragging to trash

**Slot Management**
- Duration presets: 15 to 120 minutes (configurable)
- Apply master duration to all open slots at once
- Real-time time label computation (HH:MM based on event start + cumulative durations)
- Support for "Open Deck" placeholder slots

**Events History**
- Save current lineup with a name (persisted to YAML)
- Load past event → restores all slots and settings
- Duplicate event → copy with new name
- Delete event → permanent removal with confirmation
- Events sortable by date

### Discord Bot Integration

**Bot Connection**
- Connect Discord bot directly from the app
- Display current bot status and auto-reconnect on disconnect
- Embedded token refresh UI

**Rich Embed Posting**
- Post lineups immediately as Discord embeds
- Embed includes: event title + volume, timestamp (Discord `<t:UNIX:F>` format), genres, full slot lineup with times
- DJ names bold, genre badges, computed slot times with timezone
- Embed color matches active theme accent
- Optional embed image (from URL or local file)

**Channel Picker**
- Dropdown list of your Discord server's text channels
- Bot must have send permissions in selected channel
- Channel validation before posting

**Scheduled Posting**
- Schedule posts for future delivery (specify date/time)
- Posts persist in `settings.json` across app restarts
- Background scheduler checks every ~100ms and fires due posts
- Resend capability for previously posted lineups

### Social Links

**Configurable Social Platforms**
- Support for: Timeline, VRCPop, X (Twitter), Instagram, Discord, VRC Group
- Add/edit/remove links per event
- Links appear formatted at bottom of output and Discord embeds
- **Persistent Links** — toggle to auto-carry Discord & VRC Group links across all events

### Multi-Format Output

Real-time side-by-side previews for all output formats:

| Format | Style | Link Conversion | Use Case |
|--------|-------|---|---|
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
- Auto-save every 5 seconds to `auto_save.json`
- On app launch, detect previous crash and offer recovery
- Save recovers full event state (all slots, settings) and restores to editor

**Window & Panel Persistence**
- Remembers window size, position between sessions
- Remembers left/right panel split position (drag handle)
- Auto-layout responsive to small windows (800×600 minimum)

**Resizable Panels**
- Left and right panel widths adjustable via drag handle
- Geometry persisted to `window_state.json`

---

## Input Shortcuts & Tips

| Input | Action |
|-------|--------|
| **↑ / ↓** on timestamp field | Shift event time ±15 minutes |
| **Shift + ↑ / ↓** on timestamp field | Shift event time ±24 hours |
| **Mouse wheel** on combo / duration spinners | Cycle values up or down |
| **Right-click** on any input | Copy/paste context menu (auto-added) |
| **Drag slot handle** | Reorder slots; times auto-compute |
| **Drag DJ card→slot** | Add DJ to slot with confirmation |
| **Drag to trash icon** | Delete slot (with visual feedback) |

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

All data files live in the application directory (resolved by `get_data_dir()`):
- **During development:** Project root (`desktop/`)
- **After PyInstaller build:** Executable's directory

| File | Format | Contents | Auto-Save? |
|------|--------|----------|-----------|
| `lineup_library.yaml` | YAML | DJ roster, genre library, saved titles | Every 500ms |
| `lineup_events.yaml` | YAML | Named event lineups (save/load history) | On save only |
| `settings.json` | JSON | Theme colors, UI scale, user presets, OAuth token | On change |
| `window_state.json` | JSON | Window geometry, panel widths | On window close |
| `auto_save.json` | JSON | Transient lineup state for crash recovery | Every 5 sec |

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

**Model publishes:**
- `"model_changed"` — Any state mutation (slot add/edit, title change, etc.)
- `"genres_changed"` — Roster genre list updated
- `"settings_changed"` — Theme or UI preference changed

---

## Debounce & Performance

Heavy operations are debounced to prevent UI lag:

| Method | Delay | Purpose |
|--------|-------|---------|
| `_schedule_update()` | 150 ms | Refresh output preview. Coalesces rapid model changes. |
| `_schedule_roster_refresh()` | 120 ms | Redraw DJ roster panel after bulk import or genre filter. |
| `_schedule_genre_refresh()` | 120 ms | Redraw genre tag list after add/delete. |
| `_schedule_save_library()` | 500 ms | Persist DJ/genre library to YAML. Avoids thrashing disk. |
| `_schedule_auto_save()` | 5000 ms | Write crash-recovery state to `auto_save.json`. |
| `_schedule_auto_event_save()` | 1500 ms | Write current event snapshot to `auto_save.json` for recovery. |

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
- Every setter publishes `"model_changed"`

**models/types.py**
- Type definitions, enums, constants

**output/output_generator.py**
- Pure stateless functions: `generate(snapshot)`, `compute_slot_times(snapshot)`, `vrcdn_convert(link, fmt)`
- No side effects; fully testable

**output/output_builder.py**
- `OutputMixin` — bridges UI state to `EventSnapshot` and triggers `OutputGenerator`
- `_build_snapshot()` — capture current editor state
- `update_output()` — refresh preview panel

**data_manager.py**
- `DataMixin` — YAML/JSON file I/O
- Load/save `/lineup_library.yaml`, `/lineup_events.yaml`
- Persist window geometry to `/window_state.json`
- Auto-save to `/auto_save.json` for crash recovery

**debounce.py**
- `DebounceMixin` — timer helpers + work queue
- `_schedule_*()` methods with configurable delays
- `process_queue()` — drain work queue each frame

**services/discord_service.py**
- `DiscordService` — bot lifecycle, embed posting
- Handle bot connection, token refresh, message sending
- Scheduled post tracking and firing

**services/discord_oauth.py**
- `DiscordOAuth` — OAuth2 local callback server
- User login flow, token caching, profile fetching

### Frontend Modules (DearPyGui widgets only)

**app.py**
- `App` class — inherits all 11 mixins
- Owns DPG lifecycle: create context → create viewport → setup → show → main loop
- Properties for data file paths (library, events, settings, auto_save)

**ui/init.py (UISetupMixin)**
- `UISetupMixin` — Full window layout
- Create viewport, left/right panels, tabs, all widgets
- Handle scroll/arrow key global events
- ~400-500 lines organizing the entire UI

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
- `hex_to_dpg()` converter for DearPyGui
- Reusable style dicts: `ENTRY`, `COMBO`, `BTN_PRIMARY`, `CARD`, etc.

**styling/fonts.py**
- Material Symbols icon mappings
- `styled_text()` helper for semantic typography
- Icon, HEADER, LABEL, BODY, MUTED, ERROR styles

**ui/widgets.py**
- Themed widget factory functions
- `add_primary_button()`, `add_danger_button()`, `add_styled_input()`, etc.
- All apply correct colors & spacing automatically

---

## Development Guidelines

### Code Style & Conventions

- **Type hints** — Use on public API functions; optional for private/mixin methods
- **Docstrings** — Module and class-level (triple-quoted)
- **Naming** — CamelCase for classes, snake_case for functions/variables, `_leading_underscore` for private
- **Widget tags** — Lowercase with underscores: `"event_title_input"`, `"slot_row_{id}"`
- **Backend rule** — NO DearPyGui imports in `src/backend/`; separate GUI concerns from business logic
- **Theme colors** — Always use `hex_to_dpg(TOKEN)` from `styling/theme.py`, never hardcode hex

### Adding a New Feature

1. **Add model state** to `LineupModel` if needed
2. **Create a mixin** in `src/frontend/mixins/` (or extend existing)
3. **Build UI** in mixin callbacks using themed widgets
4. **Subscribe to EventBus** for reactive updates
5. **Use debounce** for heavy operations (`_schedule_*()`)
6. **Test backend logic** in `tests/` against pure functions (no GUI)

### Testing Backend

```python
# Example: test_output_generator.py
from src.backend.output.output_generator import OutputGenerator
from src.backend.models.types import EventSnapshot, SlotData

def test_compute_slot_times():
    snap = EventSnapshot(
        timestamp="2026-03-16 20:00",
        slots=[SlotData("DJ A", "", 60), SlotData("DJ B", "", 30)],
    )
    times = OutputGenerator.compute_slot_times(snap)
    assert times == ["20:00", "21:00"]
```

### Performance Tips

- Don't call `update_output()` directly — use `_schedule_update()` to debounce
- Avoid nested grid/table rebuilds; rebuild only changed sections
- Cache `dpg.get_value()` results if called multiple times in one function
- Use `dpg.configure()` for batch updates on multiple widgets
- Profile with `cProfile` if you suspect hot loops

---

## Troubleshooting

### Issue: App won't start — "No module named dearpygui"
**Solution:** Ensure virtual environment is activated and `pip install -r requirements.txt` ran successfully. Try: `pip install dearpygui --upgrade`

### Issue: Discord bot won't connect
**Cause:** Invalid token or bot not added to your Discord server  
**Solution:** Verify token in [Developer Portal](https://discord.com/developers/applications). Regenerate if needed. Ensure bot has "Send Messages" and "Embed Links" permissions.

### Issue: Window too small, widgets cut off
**Cause:** Desktop too small or window minimized  
**Solution:** Resize window to at least 800×600. App auto-layouts for smaller sizes but 900×700 is recommended.

### Issue: Drag-drop not working
**Cause:** Slot row DOM structure incorrect  
**Solution:** Ensure `DragDropMixin.init()` was called during `App.__init__()`. Check that slot rows have correct tag `"slot_row_{id}"`.

### Issue: Theme doesn't apply to popups/modals
**Cause:** Popup created before theme bound  
**Solution:** All modals should be created *after* `apply_theme()` in `App.__init__()`. Global theme inheritance is automatic.

### Issue: Auto-save not restoring
**Cause:** `auto_save.json` corrupted or missing  
**Solution:** Delete `auto_save.json` and restart app. Non-recoverable data is still in `lineup_events.yaml` and `lineup_library.yaml`.

### Issue: PyInstaller build fails
**Cause:** Missing hidden imports or DearPyGui not properly detected  
**Solution:** Ensure `lineup_builder.spec` includes DearPyGui in `hiddenimports`. Try: `pip install --upgrade dearpygui pyinstaller`

### Issue: Yaml file corrupted, app won't load
**Cause:** Manual edit of YAML or unexpected shutdown mid-write  
**Solution:** Rename corrupted file (e.g., `lineup_library.yaml.bak`). App creates fresh file on next launch.

---

## File Format Reference

### lineup_library.yaml
```yaml
version: "1.0"
djs:
  - name: "DJ A"
    stream: "https://twitch.tv/dja"
    exact_link: false
    genres: ["House", "Techno"]
genres: ["House", "Techno", "Drum & Bass"]
saved_titles: ["New Year Bash", "Summer Party"]
```

### lineup_events.yaml
```yaml
version: "1.0"
events:
  - name: "Spring Finale"
    title: "Spring Finale"
    vol: "2"
    timestamp: "2026-04-15 22:00"
    slots:
      - name: "DJ A"
        genre: "House"
        duration: 60
    genres: ["House"]
    output_format: "discord"
    saved_at: "2026-03-16T15:30:00"
```

### settings.json
```json
{
  "theme_name": "Slate",
  "colors": {
    "panel_bg": "#160D2E",
    "card_bg": "#09051A",
    ...
  },
  "ui_scale": 1.0,
  "user_presets": [
    {
      "name": "My Custom Theme",
      "colors": { ... }
    }
  ],
  "discord_oauth": {
    "access_token": "...",
    "expires_at": 1234567890
  }
}
```

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
**Version:** 1.0.0
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
```
# Event Title VOL.3
# <t:1234567890:F> (<t:1234567890:R>)
## House // Techno
### LINEUP
<t:1234567890:t> | **DJ Alpha** (House)
<t:1234567950:t> | **DJ Beta** (Techno)
```

### Local (Plain Text)
```
Event Title VOL.3
2025-06-01 @ 20:00 (PST)
House // Techno
LINEUP
20:00 | DJ Alpha (House)
20:30 | DJ Beta (Techno)
```

### Quest / PC (Stream Links)
```
https://stream.vrcdn.live/live/{key}.live.ts   ← Quest (HLS)
rtspt://stream.vrcdn.live/live/{key}           ← PC (RTSP)
```
