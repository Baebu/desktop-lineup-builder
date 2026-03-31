import sys
from pathlib import Path

# Ensure src imports work
sys.path.insert(0, str(Path(__file__).parent))

from src.frontend.app import App


def main():
    # Set Windows AppUserModelID so the taskbar shows our icon, not Python's
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "baebu.lineupbuilder"
        )
        
    app = App()
    app.run()


if __name__ == "__main__":
    main()