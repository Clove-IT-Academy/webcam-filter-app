# Webcam Filter App

A local desktop app that previews one webcam and applies simple visual effects. All frame processing stays in memory on the device. Version 1 does not record, save, upload, or transmit video and does not require an account or network connection at runtime.

## Requirements

- Python 3.12 or newer (development currently uses Python 3.14.7).
- A webcam and operating system with camera permission for Python.
- OpenCV 5.0.0.93 and NumPy 2.5.3 are pinned in `pyproject.toml`.

The code has been developed on macOS 27.0, Apple Silicon. Camera access and GUI behavior have not yet been verified on a physical camera, so this is a development environment, not a completed platform support claim. Windows/Linux support and camera models remain to be confirmed.

## Set up

From this directory, create and use the project virtual environment:

```bash
python3 -m venv venv
./venv/bin/python -m pip install --upgrade pip
./venv/bin/python -m pip install -e .
```

On Windows PowerShell, use `venv\Scripts\python.exe` in place of `./venv/bin/python`.

## Run

```bash
./venv/bin/python -m webcam_filter_app.main
```

If the editable install is unavailable but dependencies are installed, run from the source package with:

```bash
PYTHONPATH=src ./venv/bin/python -m webcam_filter_app.main
```

## Controls

| Key | Effect |
| --- | --- |
| `1` | Original color |
| `2` | Grayscale |
| `3` | Shape overlay |
| `4` | Text overlay |
| `Q`/`q` or `Esc` | Quit |

The current effect and shortcuts are also shown in the preview. Closing the preview window quits the app.

## Camera troubleshooting

- If the preview cannot open, allow camera access for the terminal or Python application in operating system privacy settings.
- Close other applications using the camera and reconnect it, then restart the app.
- Camera index `0` is used by default. Camera selection is not part of v1.
- On macOS the app selects OpenCV's AVFoundation capture backend explicitly. If the preview remains black, verify the camera in Photo Booth, quit apps using it, and try launching this script from Terminal (Terminal is the permission-granting app in that case). OpenCV's macOS support for iPhone Continuity Camera may differ from built-in and USB cameras.
- After 30 consecutive frames with no nonzero pixels in a small sample, the preview displays a diagnostic suggesting camera permission, lens cover, or device checks. This is a warning, not proof of a specific cause.
- On exit or camera failure, the app releases the camera and closes the preview window.

## Privacy and support

Frames remain in process memory. The app does not write video or images, contact a server, or log image content. Logs contain only application lifecycle and operational information.

Development ran on macOS 27.0 ARM64, but physical camera and GUI behavior have not been verified. Supported operating systems, minimum versions, target camera models, responsiveness measurements, and release owner are still open decisions. Do not infer compatibility from successful installation alone.

## Development checks

Automated checks use synthetic images and fake camera/display adapters. Run them through the project virtual environment:

```bash
./venv/bin/python -m unittest discover -s tests -v
```

Manual release checks still need a physical camera on every declared supported platform: permission behavior, live preview, all controls, camera failure/disconnect, window close, and relaunch after cleanup.
