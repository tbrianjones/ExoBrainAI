"""File system watcher for projection sync."""

import logging
import sys
import threading
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.observers import Observer

from src.config import settings

logger = logging.getLogger(__name__)


class ProjectionHandler(FileSystemEventHandler):
    """Handler for file system events on projected files that triggers sync."""

    def __init__(self, debounce_seconds: float = 2.0):
        """Initialize the handler.

        Args:
            debounce_seconds: Time to wait before processing changes
        """
        super().__init__()
        self.debounce_seconds = debounce_seconds
        self._pending: dict[str, float] = {}  # file_path -> timestamp
        self._lock = threading.Lock()
        self._timer: threading.Timer | None = None
        self._last_sync_content: dict[str, str] = {}  # file_path -> content hash

    def _schedule_processing(self):
        """Schedule processing of pending changes."""
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
            self._timer = threading.Timer(self.debounce_seconds, self._process_pending)
            self._timer.start()

    def _process_pending(self):
        """Process all pending file changes."""
        # Import here to avoid circular imports
        from src.core.db import db_session
        from src.core.projection import sync_from_file

        with self._lock:
            pending = dict(self._pending)
            self._pending.clear()

        for file_path_str in pending:
            file_path = Path(file_path_str)
            if not file_path.exists():
                continue
            if file_path.name == "CLAUDE.md":
                continue

            try:
                # Read current content to check if it actually changed
                content = file_path.read_text(encoding="utf-8")
                content_hash = hash(content)

                # Skip if content matches last sync (prevents loops)
                if self._last_sync_content.get(file_path_str) == content_hash:
                    logger.debug(f"Skipping unchanged file: {file_path}")
                    continue

                logger.info(f"Syncing projected file: {file_path}")
                with db_session() as conn:
                    result = sync_from_file(conn, file_path)

                if result.success:
                    logger.info(f"Synced: {result.object_id}")
                    self._last_sync_content[file_path_str] = content_hash
                else:
                    # Log error to stderr but don't revert
                    print(f"Sync error for {file_path.name}: {result.message}", file=sys.stderr)
                    logger.warning(f"Sync failed: {result.message}")

            except Exception as e:
                print(f"Error syncing {file_path.name}: {e}", file=sys.stderr)
                logger.error(f"Error syncing {file_path}: {e}")

    def on_modified(self, event: FileSystemEvent):
        """Handle file modification events."""
        if event.is_directory:
            return

        path = Path(event.src_path)
        if path.suffix != ".md":
            return

        logger.debug(f"Projected file modified: {path}")
        with self._lock:
            self._pending[str(path)] = time.time()
        self._schedule_processing()

    def on_created(self, event: FileSystemEvent):
        """Handle file creation events (treat same as modification)."""
        if event.is_directory:
            return

        path = Path(event.src_path)
        if path.suffix != ".md":
            return

        logger.debug(f"Projected file created: {path}")
        with self._lock:
            self._pending[str(path)] = time.time()
        self._schedule_processing()


class ExoBrainWatcher:
    """File system watcher for ExoBrain data directory."""

    def __init__(self):
        """Initialize the watcher."""
        self.observer = Observer()
        self.projection_handler = ProjectionHandler(
            debounce_seconds=settings.watcher_debounce_seconds
        )
        self._running = False

    def start(self):
        """Start watching the data directory."""
        if self._running:
            logger.warning("Watcher already running")
            return

        # Ensure directories exist
        settings.projected_dir.mkdir(parents=True, exist_ok=True)

        # Watch projected directory for bidirectional sync
        self.observer.schedule(
            self.projection_handler,
            str(settings.projected_dir),
            recursive=True,
        )
        logger.info(f"Watching projected directory: {settings.projected_dir}")

        self.observer.start()
        self._running = True
        logger.info("ExoBrain watcher started")

    def stop(self):
        """Stop watching."""
        if not self._running:
            return

        self.observer.stop()
        self.observer.join()
        self._running = False
        logger.info("ExoBrain watcher stopped")

    def is_running(self) -> bool:
        """Check if watcher is running."""
        return self._running
