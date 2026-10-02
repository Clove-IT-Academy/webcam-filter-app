"""OpenCV preview and keyboard/window input adapter."""

import logging

import cv2
import numpy as np
from numpy.typing import NDArray

logger = logging.getLogger(__name__)


class Display:
    """Owns one OpenCV window and exposes a narrow UI boundary."""

    def __init__(self, window_name: str) -> None:
        if not window_name.strip():
            raise ValueError("Window name cannot be empty.")
        self._window_name = window_name
        self._initialized = False

    def initialize(self) -> None:
        """Create a resizable preview window."""

        cv2.namedWindow(self._window_name, cv2.WINDOW_NORMAL)
        self._initialized = True

    def show_frame(
        self,
        frame: NDArray[np.uint8],
        effect_label: str,
        warning: str | None = None,
    ) -> None:
        """Draw controls and any diagnostic hint before showing the processed frame."""

        if not self._initialized:
            raise RuntimeError("Display window has not been initialized.")
        height, width = frame.shape[:2]
        panel_height = min(86 if warning else 58, height)
        cv2.rectangle(frame, (0, 0), (width, panel_height), (24, 24, 24), thickness=-1)
        label = effect_label.replace("_", " ").title()
        cv2.putText(
            frame,
            f"Effect: {label}  |  1 Original  2 Gray  3 Shape  4 Text  |  Q / Esc: Quit",
            (10, min(panel_height - 8, 28)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (255, 255, 255),
            thickness=1,
            lineType=cv2.LINE_AA,
        )
        if warning and panel_height >= 52:
            cv2.putText(
                frame,
                warning,
                (10, min(panel_height - 8, 58)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (80, 190, 255),
                thickness=1,
                lineType=cv2.LINE_AA,
            )
        cv2.imshow(self._window_name, frame)

    def read_key(self, delay_ms: int = 1) -> int:
        """Poll keyboard input without waiting long enough to stall the preview."""

        return cv2.waitKey(delay_ms) & 0xFF

    def is_open(self) -> bool:
        """Return false if the user closed the window or OpenCV reports it gone."""

        if not self._initialized:
            return False
        try:
            return cv2.getWindowProperty(self._window_name, cv2.WND_PROP_VISIBLE) >= 1
        except cv2.error:
            return False

    def show_error(self, message: str, delay_ms: int = 2200) -> None:
        """Display a short startup error briefly when the window is available."""

        if not self._initialized:
            return
        canvas = np.zeros((120, 720, 3), dtype=np.uint8)
        cv2.putText(
            canvas,
            "Camera unavailable",
            (18, 42),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            thickness=2,
            lineType=cv2.LINE_AA,
        )
        cv2.putText(
            canvas,
            message[:88],
            (18, 82),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            (220, 220, 220),
            thickness=1,
            lineType=cv2.LINE_AA,
        )
        cv2.imshow(self._window_name, canvas)
        cv2.waitKey(delay_ms)

    def close(self) -> None:
        """Destroy the window once; safe on all application shutdown paths."""

        if not self._initialized:
            return
        self._initialized = False
        try:
            cv2.destroyWindow(self._window_name)
        except cv2.error:
            logger.debug("Preview window was already closed.")
