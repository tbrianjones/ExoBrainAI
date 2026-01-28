"""File system watcher for automatic staging and projection sync."""

import logging
import sqlite3
import sys
import threading
import time
from collections import defaultdict
from pathlib import Path

from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.observers import Observer

from src.config import settings

logger = logging.getLogger(__name__)


class StagingHandler(FileSystemEventHandler):
    """Handler for file system events that triggers staging."""

    def __init__(self, debounce_seconds: float = 2.0):
        """Initialize the handler.

        Args:
            debounce_seconds: Time to wait before processing changes
        """
        super().__init__()
        self.debounce_seconds = debounce_seconds
        self._pending: dict[str, float] = {}  # doc_id -> timestamp
        self._lock = threading.Lock()
        self._timer: threading.Timer | None = None

    def _schedule_processing(self):
        """Schedule processing of pending changes."""
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
            self._timer = threading.Timer(self.debounce_seconds, self._process_pending)
            self._timer.start()

    def _process_pending(self):
        """Process all pending document changes."""
        with self._lock:
            pending = dict(self._pending)
            self._pending.clear()

        for doc_id in pending:
            try:
                logger.info(f"Staging document: {doc_id}")
                result = stage_doc(doc_id)
                if result:
                    logger.info(f"Staged: {result}")
                else:
                    logger.warning(f"Could not stage {doc_id}: raw doc not found")
            except Exception as e:
                logger.error(f"Error staging {doc_id}: {e}")

    def _extract_doc_id(self, path: str) -> str | None:
        """Extract document ID from a file path.

        Args:
            path: File path

        Returns:
            Document ID if valid, None otherwise
        """
        p = Path(path)
        if p.suffix == ".md":
            return p.stem
        return None

    def _handle_raw_change(self, event: FileSystemEvent):
        """Handle changes to raw documents."""
        doc_id = self._extract_doc_id(event.src_path)
        if doc_id:
            with self._lock:
                self._pending[doc_id] = time.time()
            self._schedule_processing()

    def _handle_overlay_change(self, event: FileSystemEvent):
        """Handle changes to overlay files.

        For overlay changes, we need to re-stage all affected documents.
        For simplicity, we trigger a full re-stage on overlay changes.
        """
        # In a more sophisticated implementation, we would parse the
        # overlay file to find affected doc_ids. For now, we just log it.
        logger.info(f"Overlay changed: {event.src_path}")
        # TODO: Parse overlay file and stage affected documents

    def on_created(self, event: FileSystemEvent):
        """Handle file creation events."""
        if event.is_directory:
            return

        path = Path(event.src_path)
        if str(settings.raw_dir) in str(path):
            logger.debug(f"Raw file created: {path}")
            self._handle_raw_change(event)
        elif str(settings.overlay_dir) in str(path):
            logger.debug(f"Overlay file created: {path}")
            self._handle_overlay_change(event)

    def on_modified(self, event: FileSystemEvent):
        """Handle file modification events."""
        if event.is_directory:
            return

        path = Path(event.src_path)
        if str(settings.raw_dir) in str(path):
            logger.debug(f"Raw file modified: {path}")
            self._handle_raw_change(event)
        elif str(settings.overlay_dir) in str(path):
            logger.debug(f"Overlay file modified: {path}")
            self._handle_overlay_change(event)

    def on_deleted(self, event: FileSystemEvent):
        """Handle file deletion events."""
        if event.is_directory:
            return

        path = Path(event.src_path)
        if str(settings.raw_dir) in str(path):
            doc_id = self._extract_doc_id(event.src_path)
            if doc_id:
                logger.info(f"Raw file deleted: {doc_id}")
                # Optionally delete the staged version
                staged_path = settings.staged_dir / f"{doc_id}.txt"
                if staged_path.exists():
                    staged_path.unlink()
                    logger.info(f"Deleted staged file: {staged_path}")


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
        from src.core.db import get_connection
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
                with get_connection() as conn:
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
        self.staging_handler = StagingHandler(
            debounce_seconds=settings.watcher_debounce_seconds
        )
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
        settings.raw_dir.mkdir(parents=True, exist_ok=True)
        settings.overlay_dir.mkdir(parents=True, exist_ok=True)
        settings.projected_dir.mkdir(parents=True, exist_ok=True)

        # Watch raw directory (legacy staging)
        self.observer.schedule(
            self.staging_handler,
            str(settings.raw_dir),
            recursive=False,
        )
        logger.info(f"Watching raw directory: {settings.raw_dir}")

        # Watch overlay directory (legacy staging)
        self.observer.schedule(
            self.staging_handler,
            str(settings.overlay_dir),
            recursive=False,
        )
        logger.info(f"Watching overlay directory: {settings.overlay_dir}")

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
