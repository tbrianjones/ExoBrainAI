"""Scheduled operations for ExoBrain."""

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Callable

logger = logging.getLogger(__name__)


class Scheduler:
    """Simple scheduler for periodic tasks."""

    def __init__(self):
        """Initialize the scheduler."""
        self._tasks: dict[str, dict] = {}
        self._running = False
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    def add_task(
        self,
        name: str,
        func: Callable,
        interval_seconds: int,
        run_immediately: bool = False,
    ):
        """Add a periodic task.

        Args:
            name: Task identifier
            func: Function to call
            interval_seconds: Seconds between runs
            run_immediately: If True, run once immediately on start
        """
        with self._lock:
            self._tasks[name] = {
                "func": func,
                "interval": interval_seconds,
                "last_run": None if run_immediately else datetime.now(),
                "run_immediately": run_immediately,
            }
        logger.info(f"Added scheduled task: {name} (every {interval_seconds}s)")

    def remove_task(self, name: str):
        """Remove a scheduled task.

        Args:
            name: Task identifier
        """
        with self._lock:
            if name in self._tasks:
                del self._tasks[name]
                logger.info(f"Removed scheduled task: {name}")

    def _run_loop(self):
        """Main scheduler loop."""
        while self._running:
            now = datetime.now()

            with self._lock:
                tasks_to_run = []
                for name, task in self._tasks.items():
                    last_run = task["last_run"]
                    interval = timedelta(seconds=task["interval"])

                    if last_run is None or (now - last_run) >= interval:
                        tasks_to_run.append((name, task))

            for name, task in tasks_to_run:
                try:
                    logger.info(f"Running scheduled task: {name}")
                    task["func"]()
                    with self._lock:
                        self._tasks[name]["last_run"] = now
                except Exception as e:
                    logger.error(f"Error in scheduled task {name}: {e}")

            time.sleep(1)  # Check every second

    def start(self):
        """Start the scheduler."""
        if self._running:
            logger.warning("Scheduler already running")
            return

        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("Scheduler started")

    def stop(self):
        """Stop the scheduler."""
        if not self._running:
            return

        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Scheduler stopped")

    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self._running


# Index rebuild lock to prevent concurrent indexing
_index_lock = threading.Lock()


def with_index_lock(func: Callable) -> Callable:
    """Decorator to ensure only one index operation runs at a time."""

    def wrapper(*args, **kwargs):
        if not _index_lock.acquire(blocking=False):
            logger.warning("Index operation already in progress, skipping")
            return None
        try:
            return func(*args, **kwargs)
        finally:
            _index_lock.release()

    return wrapper
