"""Validated, deliberately small configuration for the v1 application."""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from webcam_filter_app.effects import Effect


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Runtime settings with safe defaults and immutable effect shortcuts."""

    camera_index: int = 0
    window_name: str = "Webcam Filter App"
    effect_keys: Mapping[int, Effect] = MappingProxyType(
        {
            ord("1"): Effect.ORIGINAL,
            ord("2"): Effect.GRAYSCALE,
            ord("3"): Effect.SHAPE,
            ord("4"): Effect.TEXT,
        }
    )
    quit_keys: tuple[int, ...] = (ord("q"), ord("Q"), 27)

    def __post_init__(self) -> None:
        if isinstance(self.camera_index, bool) or not isinstance(self.camera_index, int):
            raise ValueError("Camera index must be a non-negative integer.")
        if self.camera_index < 0:
            raise ValueError("Camera index must be a non-negative integer.")
        if not self.window_name.strip():
            raise ValueError("Window name cannot be empty.")

        keys = tuple(self.effect_keys)
        if any(isinstance(key, bool) or not isinstance(key, int) for key in keys):
            raise ValueError("Effect shortcuts must be integer key codes.")
        if not self.quit_keys or any(
            isinstance(key, bool) or not isinstance(key, int) for key in self.quit_keys
        ):
            raise ValueError("At least one integer quit shortcut is required.")
        if len(set(keys)) != len(keys):
            raise ValueError("Effect shortcuts must be unique.")
        if len(set(self.quit_keys)) != len(self.quit_keys):
            raise ValueError("Quit shortcuts must be unique.")
        if set(keys).intersection(self.quit_keys):
            raise ValueError("Effect shortcuts cannot conflict with quit shortcuts.")
        if set(self.effect_keys.values()) != set(Effect):
            raise ValueError("Each supported effect must have exactly one shortcut.")
        object.__setattr__(self, "effect_keys", MappingProxyType(dict(self.effect_keys)))

    @property
    def key_to_effect(self) -> Mapping[int, Effect]:
        """Return the validated key mapping without allowing mutation."""

        return self.effect_keys
