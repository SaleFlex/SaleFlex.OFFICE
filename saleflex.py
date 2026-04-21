"""
SaleFlex.OFFICE - Desktop back-office application entry point.
"""

from __future__ import annotations

import os
import sys


_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if os.getcwd() != _SCRIPT_DIR:
    os.chdir(_SCRIPT_DIR)

_MIN_PYTHON = (3, 11)
if sys.version_info < _MIN_PYTHON:
    sys.exit(
        f"SaleFlex.OFFICE requires Python {_MIN_PYTHON[0]}.{_MIN_PYTHON[1]} or higher.\n"
        f"Current interpreter: Python {sys.version}"
    )


def main() -> int:
    """Run the Office application lifecycle."""
    from core.logger import get_logger
    from office.manager.application import OfficeApplication
    from settings.settings import Settings

    logger = get_logger(__name__)
    version = Settings().app_version

    logger.info("=" * 60)
    logger.info("Starting SaleFlex.OFFICE v%s", version)
    logger.info("Python %s on %s", sys.version.split()[0], sys.platform)
    logger.info("Working directory: %s", os.getcwd())
    logger.info("=" * 60)

    try:
        app = OfficeApplication()
        return app.run()
    except Exception:
        logger.critical("Unhandled exception - application terminated", exc_info=True)
        return 1
    finally:
        logger.info("SaleFlex.OFFICE v%s - shutdown complete", version)


if __name__ == "__main__":
    raise SystemExit(main())
