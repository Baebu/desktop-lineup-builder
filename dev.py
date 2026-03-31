#!/usr/bin/env python3
"""
Development script that monitors code changes and auto-restarts the app.
"""

import subprocess
import sys
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class RestartHandler(FileSystemEventHandler):
    def __init__(self, script_path):
        self.script_path = script_path
        self.process = None
        self.start_process()

    def start_process(self):
        if self.process:
            self.process.terminate()
            self.process.wait()
        print("Starting app...")
        self.process = subprocess.Popen([sys.executable, self.script_path])

    def on_modified(self, event):
        if str(event.src_path).endswith('.py'):
            print(f"Detected change in {event.src_path}, restarting...")
            self.start_process()


def main():
    # Since we're now in desktop/, main.py is in the same directory
    script_path = Path(__file__).parent / "main.py"
    if not script_path.exists():
        print(f"Error: {script_path} not found")
        sys.exit(1)

    # Monitor the src directory
    watch_path = Path(__file__).parent / "src"
    if not watch_path.exists():
        print(f"Error: {watch_path} not found")
        sys.exit(1)

    event_handler = RestartHandler(str(script_path))
    observer = Observer()
    observer.schedule(event_handler, str(watch_path), recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
