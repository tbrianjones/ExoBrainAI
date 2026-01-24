"""ExoBrain file watcher entry point."""

import logging
import time

from src.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """Run the file watcher."""
    logger.info(f"Starting ExoBrain watcher for {settings.data_dir}")
    logger.info(f"Watching: {settings.raw_dir}")
    logger.info(f"Watching: {settings.overlay_dir}")

    # Placeholder: actual watcher implementation in Phase 7
    while True:
        time.sleep(60)
        logger.debug("Watcher heartbeat")


if __name__ == "__main__":
    main()
