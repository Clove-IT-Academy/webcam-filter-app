"""App-flow tests use fake adapters and synthetic frames only."""

import unittest

import numpy as np

from webcam_filter_app.app import App
from webcam_filter_app.camera import CameraError
from webcam_filter_app.config import AppConfig
from webcam_filter_app.effects import Effect


class FakeCamera:
    def __init__(self, frames: list[tuple[bool, np.ndarray | None]]) -> None:
        self.frames = iter(frames)
        self.opened = False
        self.released = False

    def open(self) -> None:
        self.opened = True

    def read(self) -> tuple[bool, np.ndarray | None]:
        return next(self.frames)

    def release(self) -> None:
        self.released = True


class FakeDisplay:
    def __init__(self, keys: list[int] | None = None) -> None:
        self.keys = iter(keys or [])
        self.initialized = False
        self.closed = False
        self.errors: list[str] = []
        self.frames: list[tuple[np.ndarray, str, str | None]] = []
        self.open_checks = 0

    def initialize(self) -> None:
        self.initialized = True

    def is_open(self) -> bool:
        self.open_checks += 1
        return self.open_checks <= len(self.frames) + 1

    def show_frame(
        self,
        frame: np.ndarray,
        effect_label: str,
        warning: str | None = None,
    ) -> None:
        self.frames.append((frame, effect_label, warning))

    def read_key(self, delay_ms: int = 1) -> int:
        return next(self.keys, -1)

    def show_error(self, message: str, delay_ms: int = 2200) -> None:
        self.errors.append(message)

    def close(self) -> None:
        self.closed = True


class AppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.frame = np.zeros((48, 64, 3), dtype=np.uint8)

    def test_shortcut_selects_effect_and_quit_cleans_up(self) -> None:
        camera = FakeCamera([(True, self.frame), (True, self.frame)])
        display = FakeDisplay([ord("2"), ord("q")])
        app = App(camera=camera, display=display)

        app.run()

        self.assertEqual([label for _, label, _ in display.frames], ["original", "grayscale"])
        self.assertTrue(camera.released)
        self.assertTrue(display.closed)

    def test_persistent_black_frames_show_a_safe_diagnostic(self) -> None:
        camera = FakeCamera([(True, self.frame.copy()) for _ in range(30)])
        display = FakeDisplay([-1] * 29 + [ord("q")])

        App(camera=camera, display=display).run()

        self.assertIsNone(display.frames[28][2])
        self.assertIn("No picture detected", display.frames[29][2] or "")

    def test_failed_read_never_reaches_processor_and_cleans_up(self) -> None:
        camera = FakeCamera([(False, None)])
        display = FakeDisplay()
        app = App(camera=camera, display=display, processor=lambda *_: self.fail("invalid frame processed"))

        with self.assertRaises(CameraError):
            app.run()

        self.assertTrue(camera.released)
        self.assertTrue(display.closed)

    def test_camera_open_error_is_shown_and_cleaned_up(self) -> None:
        class FailedCamera(FakeCamera):
            def open(self) -> None:
                raise CameraError("Camera unavailable.")

        camera = FailedCamera([])
        display = FakeDisplay()
        app = App(camera=camera, display=display)

        with self.assertRaises(CameraError):
            app.run()

        self.assertEqual(display.errors, ["Camera unavailable."])
        self.assertTrue(camera.released)
        self.assertTrue(display.closed)

    def test_invalid_camera_index_is_rejected(self) -> None:
        for camera_index in (-1, True, 1.5):
            with self.subTest(camera_index=camera_index):
                with self.assertRaises(ValueError):
                    AppConfig(camera_index=camera_index)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
