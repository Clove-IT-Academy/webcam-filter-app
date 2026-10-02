"""Application lifecycle, effect selection, and bounded preview loop."""

import logging
from collections.abc import Callable

import numpy as np

from webcam_filter_app.camera import Camera, CameraError
from webcam_filter_app.config import AppConfig
from webcam_filter_app.display import Display
from webcam_filter_app.effects import Effect, apply_effect, validate_frame

logger = logging.getLogger(__name__)
EffectProcessor = Callable[[object, Effect], np.ndarray]
BLACK_FRAME_WARNING_AFTER = 30
BLACK_FRAME_WARNING = "No picture detected: check camera permission, lens cover, or camera device."


def _sample_has_image_data(frame: np.ndarray) -> bool:
    """Check a small grid for nonzero pixels without scanning/copying full frames."""

    height, width = frame.shape[:2]
    row_step = max(1, height // 12)
    column_step = max(1, width // 16)
    return bool(np.any(frame[::row_step, ::column_step]))


class App:
    """Coordinate camera, frame processing, keyboard controls, and cleanup."""

    def __init__(
        self,
        config: AppConfig | None = None,
        camera: Camera | None = None,
        display: Display | None = None,
        processor: EffectProcessor = apply_effect,
    ) -> None:
        self.config = config or AppConfig()
        self.camera = camera or Camera(self.config.camera_index)
        self.display = display or Display(self.config.window_name)
        self.processor = processor
        self.selected_effect = Effect.ORIGINAL
        self._consecutive_black_frames = 0

    def run(self) -> None:
        """Run until the user quits or a camera/display failure occurs."""

        try:
            self.display.initialize()
            try:
                self.camera.open()
            except CameraError as error:
                self.display.show_error(str(error))
                raise

            logger.info("Preview started.")
            while self.display.is_open():
                success, frame = self.camera.read()
                if not success or frame is None:
                    raise CameraError("The camera stopped providing frames. Check the connection and restart the app.")
                try:
                    validate_frame(frame)
                except ValueError as error:
                    raise CameraError("The camera returned an unsupported image frame.") from error

                if _sample_has_image_data(frame):
                    self._consecutive_black_frames = 0
                else:
                    self._consecutive_black_frames += 1
                warning = (
                    BLACK_FRAME_WARNING
                    if self._consecutive_black_frames >= BLACK_FRAME_WARNING_AFTER
                    else None
                )

                processed = self.processor(frame, self.selected_effect)
                self.display.show_frame(processed, self.selected_effect.value, warning=warning)
                key = self.display.read_key(1)
                if key in self.config.quit_keys:
                    break
                selected = self.config.key_to_effect.get(key)
                if selected is not None:
                    self.selected_effect = selected
        finally:
            self._cleanup()

    def _cleanup(self) -> None:
        """Always release camera and preview resources, even if one cleanup fails."""

        try:
            self.camera.release()
        finally:
            self.display.close()
            logger.info("Preview stopped.")
