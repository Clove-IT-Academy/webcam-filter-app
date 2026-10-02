"""Command-line entry point for the local webcam filter app."""

import logging
import sys

from webcam_filter_app.app import App
from webcam_filter_app.camera import CameraError


def main() -> int:
    """Run the desktop preview and return a conventional process exit code."""

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
        App().run()
    except CameraError as error:
        print(f"Camera error: {error}", file=sys.stderr)
        return 1
    except Exception:
        logging.exception("The app stopped because of an unexpected error.")
        print("The app stopped unexpectedly. See the error details above.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
