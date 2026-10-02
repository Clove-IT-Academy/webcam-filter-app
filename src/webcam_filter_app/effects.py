"""Pure frame validation and visual effects; no camera or window management."""

from enum import Enum

import cv2
import numpy as np
from numpy.typing import NDArray

Frame = NDArray[np.uint8]
MAX_FRAME_PIXELS = 33_177_600  # Bounds work and memory for unusually large inputs.
MAX_FRAME_EDGE = 8_192


class Effect(str, Enum):
    """Effects supported by the first release."""

    ORIGINAL = "original"
    GRAYSCALE = "grayscale"
    SHAPE = "shape"
    TEXT = "text"


def validate_frame(frame: object) -> Frame:
    """Validate a BGR uint8 frame before passing it to OpenCV operations."""

    if not isinstance(frame, np.ndarray):
        raise ValueError("Camera returned no valid image frame.")
    if frame.dtype != np.uint8:
        raise ValueError("Camera frame has an unsupported pixel format.")
    if frame.ndim != 3 or frame.shape[2] != 3:
        raise ValueError("Camera frame must be a three-channel color image.")

    height, width, _ = frame.shape
    if height < 1 or width < 1 or height > MAX_FRAME_EDGE or width > MAX_FRAME_EDGE:
        raise ValueError("Camera frame dimensions are outside the supported range.")
    if height * width > MAX_FRAME_PIXELS:
        raise ValueError("Camera frame is too large to process safely.")
    return frame


def apply_effect(frame: object, effect: Effect) -> Frame:
    """Apply one deterministic effect to a valid BGR frame.

    The input is never modified. Original and overlay effects make one bounded
    copy so callers retain the captured frame and display annotations can be
    applied to the returned result without changing the source.
    """

    source = validate_frame(frame)
    try:
        selected = Effect(effect)
    except (TypeError, ValueError) as error:
        raise ValueError(f"Unsupported effect: {effect!r}.") from error

    if selected is Effect.ORIGINAL:
        return source.copy()
    if selected is Effect.GRAYSCALE:
        return cv2.cvtColor(source, cv2.COLOR_BGR2GRAY)

    output = source.copy()
    height, width = output.shape[:2]
    if selected is Effect.SHAPE:
        center = (width // 2, height // 2)
        radius = max(12, min(width, height) // 8)
        cv2.circle(output, center, radius, (40, 220, 255), thickness=4, lineType=cv2.LINE_AA)
    elif selected is Effect.TEXT:
        baseline_y = max(36, min(height - 12, height // 8))
        cv2.putText(
            output,
            "Webcam Filter",
            (16, baseline_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            thickness=2,
            lineType=cv2.LINE_AA,
        )
    return output
