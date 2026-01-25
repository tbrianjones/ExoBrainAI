"""File system watcher for automatic staging."""

import logging
import threading
import time
from collections import defaultdict
from pathlib import Path

from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.observers import Observer

from src.config import settings
from src.core.stager import stage_doc

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


class ExoBrainWatcher:
    """File system watcher for ExoBrain data directory."""

    def __init__(self):
        """Initialize the watcher."""
        self.observer = Observer()
        self.handler = StagingHandler(
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

        # Watch raw directory
        self.observer.schedule(
            self.handler,
            str(settings.raw_dir),
            recursive=False,
        )
        logger.info(f"Watching raw directory: {settings.raw_dir}")

        # Watch overlay directory
        self.observer.schedule(
            self.handler,
            str(settings.overlay_dir),
            recursive=False,
        )
        logger.info(f"Watching overlay directory: {settings.overlay_dir}")

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
