"""ExoBrain file watcher entry point."""

import logging
import signal
import sys
import time

from src.config import settings
from src.watcher.watcher import ExoBrainWatcher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """Run the file watcher."""
    logger.info(f"Starting ExoBrain watcher for {settings.data_dir}")

    # Ensure directories exist
    settings.ensure_dirs()

    watcher = ExoBrainWatcher()

    # Handle shutdown signals
    def shutdown(signum, frame):
        logger.info("Shutdown signal received")
        watcher.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # Start the watcher
    watcher.start()

    # Keep the main thread alive
    try:
        while True:
            time.sleep(60)
            logger.debug("Watcher heartbeat")
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        watcher.stop()


if __name__ == "__main__":
    main()
