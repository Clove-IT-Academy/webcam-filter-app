"""Small OpenCV camera adapter with explicit ownership and cleanup."""

import logging
import sys

import cv2
import numpy as np
from numpy.typing import NDArray

logger = logging.getLogger(__name__)


class CameraError(RuntimeError):
    """A camera could not be opened or did not provide a frame."""


class Camera:
    """Own one camera capture handle for the lifetime of the application."""

    def __init__(self, camera_index: int = 0) -> None:
        if isinstance(camera_index, bool) or not isinstance(camera_index, int) or camera_index < 0:
            raise ValueError("Camera index must be a non-negative integer.")
        self._camera_index = camera_index
        self._capture: cv2.VideoCapture | None = None

    def open(self) -> None:
        """Open the configured camera once, failing with a useful safe message."""

        if self._capture is not None and self._capture.isOpened():
            return
        self.release()
        capture: cv2.VideoCapture | None = None
        try:
            backend = cv2.CAP_AVFOUNDATION if sys.platform == "darwin" else cv2.CAP_ANY
            capture = cv2.VideoCapture(self._camera_index, backend)
            if not capture.isOpened():
                capture.release()
                capture = None
                raise CameraError(
                    "Could not open the camera. Check camera permissions, connection, and that it is not in use."
                )
        except cv2.error as error:
            if capture is not None:
                capture.release()
            raise CameraError("Could not initialize the camera. Check its permissions and availability.") from error
        self._capture = capture
        try:
            backend_name = capture.getBackendName()
        except cv2.error:
            backend_name = "unknown"
        logger.info("Camera opened (index=%d, backend=%s).", self._camera_index, backend_name)

    def read(self) -> tuple[bool, NDArray[np.uint8] | None]:
        """Return the next frame; failed or missing frames are never fabricated."""

        if self._capture is None:
            return False, None
        try:
            if not self._capture.isOpened():
                return False, None
            success, frame = self._capture.read()
        except cv2.error as error:
            logger.warning("Camera frame read failed.")
            raise CameraError("The camera stopped providing frames.") from error
        if not success or frame is None:
            return False, None
        return True, frame

    def release(self) -> None:
        """Release the capture handle; repeated cleanup calls are safe."""

        capture, self._capture = self._capture, None
        if capture is not None:
            try:
                capture.release()
            except cv2.error:
                logger.warning("Camera release reported an OpenCV error.")
            else:
                logger.info("Camera released.")
