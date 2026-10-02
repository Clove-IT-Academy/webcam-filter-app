"""Synthetic-frame unit tests; never use physical camera footage as a fixture."""

import unittest

import numpy as np

from webcam_filter_app.effects import Effect, apply_effect, validate_frame


class EffectsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.frame = np.full((120, 160, 3), 128, dtype=np.uint8)
        self.original = self.frame.copy()

    def test_each_effect_returns_displayable_output_without_mutating_input(self) -> None:
        for effect in Effect:
            with self.subTest(effect=effect):
                result = apply_effect(self.frame, effect)
                self.assertEqual(result.shape[:2], self.frame.shape[:2])
                self.assertEqual(result.dtype, np.uint8)
                self.assertTrue(np.array_equal(self.frame, self.original))

    def test_grayscale_returns_single_channel_image(self) -> None:
        self.assertEqual(apply_effect(self.frame, Effect.GRAYSCALE).ndim, 2)

    def test_invalid_frame_shapes_and_pixel_formats_are_rejected(self) -> None:
        invalid_frames = [None, np.zeros((10, 10), dtype=np.uint8), np.zeros((10, 10, 4), dtype=np.uint8)]
        for frame in invalid_frames:
            with self.subTest(frame=type(frame)):
                with self.assertRaises(ValueError):
                    validate_frame(frame)
        with self.assertRaises(ValueError):
            validate_frame(np.zeros((10, 10, 3), dtype=np.float32))

    def test_oversized_dimensions_are_rejected(self) -> None:
        frame = np.zeros((8193, 1, 3), dtype=np.uint8)
        with self.assertRaises(ValueError):
            validate_frame(frame)

    def test_unknown_effect_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            apply_effect(self.frame, "sepia")  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
