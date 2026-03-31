import os
import sys


def get_assets_dir() -> str:
    """Return the directory containing the assets folder."""
    if getattr(sys, "frozen", False):
        # When frozen, PyInstaller unpacks to sys._MEIPASS in one-file mode
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    # In development: desktop/src/frontend/utils.py → 3 levels up → desktop/
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _project_root() -> str:
    """Return the project root (parent of desktop/)."""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def get_data_dir() -> str:
    """Return the directory where runtime data files live."""
    if getattr(sys, "frozen", False):
        # When bundled, use exe directory so user config saves next to the executable
        return os.path.dirname(sys.executable)
    # desktop/src/frontend/utils.py → desktop/
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_icon_path() -> str | None:
    """Return path to assets/icon.ico, converting from PNG on first run."""
    base = get_assets_dir()
    ico_path = os.path.join(base, "assets", "icon.ico")
    if os.path.exists(ico_path):
        return ico_path
    png_path = os.path.join(base, "assets", "icon.png")
    if not os.path.exists(png_path):
        return None
    try:
        from PIL import Image
        img = Image.open(png_path).convert("RGBA")
        sizes =[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        img.save(ico_path, format="ICO", sizes=sizes)
        return ico_path
    except Exception as e:
        print(f"[icon] Could not convert PNG to ICO: {e}")
        return None