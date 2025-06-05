import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from typing import Callable, List

class ScreenshotHandler(FileSystemEventHandler):
    def __init__(self, callback: Callable[[str], None], supported_extensions: List[str] = ['.png', '.jpg', '.jpeg']):
        self.callback = callback
        self.supported_extensions = supported_extensions
        self.processing_files = set()

    def on_created(self, event):
        if not event.is_directory:
            file_path = event.src_path
            if self._is_supported_file(file_path) and file_path not in self.processing_files:
                self.processing_files.add(file_path)
                try:
                    # Wait for file to be completely written
                    max_attempts = 10
                    attempt = 0
                    while attempt < max_attempts:
                        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                            # Additional wait to ensure file is completely written
                            time.sleep(1.0)
                            try:
                                # Try to open the file to verify it's readable
                                with open(file_path, 'rb') as f:
                                    f.read(1)
                                break
                            except:
                                time.sleep(0.5)
                        else:
                            time.sleep(0.5)
                        attempt += 1
                    
                    if attempt < max_attempts:
                        self.callback(file_path)
                    else:
                        print(f"File not ready after {max_attempts} attempts: {file_path}")
                finally:
                    self.processing_files.remove(file_path)

    def _is_supported_file(self, file_path: str) -> bool:
        """Check if the file has a supported extension."""
        return any(file_path.lower().endswith(ext) for ext in self.supported_extensions)

class FileWatcher:
    def __init__(self, watch_dir: str, callback: Callable[[str], None], supported_extensions: List[str] = ['.png', '.jpg', '.jpeg']):
        self.watch_dir = watch_dir
        self.callback = callback
        self.supported_extensions = supported_extensions
        self.observer = None
        self.handler = None

    def start(self):
        """Start watching the directory for new files."""
        if not os.path.exists(self.watch_dir):
            print(f"Watch directory does not exist: {self.watch_dir}")
            return False

        self.handler = ScreenshotHandler(self.callback, self.supported_extensions)
        self.observer = Observer()
        self.observer.schedule(self.handler, self.watch_dir, recursive=False)
        self.observer.start()
        print(f"Started watching directory: {self.watch_dir}")
        return True

    def stop(self):
        """Stop watching the directory."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            print("Stopped watching directory") 