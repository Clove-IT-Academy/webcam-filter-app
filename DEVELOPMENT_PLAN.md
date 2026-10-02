# Webcam Filter App - Development Plan

## Purpose

This document turns `Webcam_Filter_App_System_Architecture.pdf` into a start-to-finish implementation plan. Use it as shared context during development, review progress against the phase exit criteria, and update it when a decision changes.

The plan follows the architecture's version 1 scope: a local Python desktop application using OpenCV, one active/default camera, one preview, original/grayscale/shape/text effects, simple keyboard controls, in-memory frame processing, and no recording, upload, analytics, account, backend, or database.

## Product outcome

A first-time user can install and launch the app, see a live webcam preview, switch among the supported effects, and quit through either the keyboard or the window close control. When camera access or frame capture fails, the app explains the problem and releases resources cleanly. The release has repeatable setup instructions, tests, an explicit supported-platform statement, and a version identifier.

## Architecture to preserve

| Area | Responsibility / contract |
| --- | --- |
| `main.py` | Minimal executable entry point; invokes application startup and reports a final safe error if startup cannot proceed. |
| `app.py` | Owns lifecycle, main loop, selected effect, controls, error handling, and cleanup order. |
| `camera.py` | Wraps OpenCV camera open/read/status/release. Never processes effects or owns UI policy. |
| `effects.py` | Small frame transformations. Input is a valid image array plus an effect identifier; output is a displayable frame. No camera/window calls. Preserve the input when practical. |
| `display.py` | Wraps preview window, key polling, window-close detection where supported, and window cleanup. |
| `config.py` | Safe validated defaults such as camera index, effect mapping, and shortcuts. Keep configuration simple and documented. |
| Logging | Operational lifecycle/error facts only. Never log frame pixels, credentials, or unnecessary personal information. |

Keep the app single-process and local. Every normal exit and handled failure must converge on cleanup that releases the camera and closes OpenCV windows. Never pass a failed or invalid frame to an effect.

## Decisions required before implementation

Record answers in the decision log below before claiming a platform supported. A short camera spike may inform these decisions.

1. Which operating system(s) and minimum versions are in the first release?
2. Which target machines/cameras are available for real integration checks?
3. Is the default camera index sufficient for v1, or is basic camera selection an explicit requirement? Default to one documented index unless user needs say otherwise.
4. Which key bindings will be used for the effects and quit? Keep them few, consistent, visible in the preview hint, and documented.
5. Is source-based execution sufficient for the first handoff, or is a standalone executable required? Treat packaging as optional follow-on work after the app works from source.
6. What Python version range will be supported? Select it based on target platform/OpenCV compatibility and pin the tested dependency set.
7. Who owns issue triage and dependency updates, and where should users report problems?

Do not expand v1 to face recognition, identity inference, multiple cameras, recording, screenshots, cloud processing, accounts, analytics, or network communication. Re-scope such a feature with new requirements and privacy/security review first.

## Step-by-step delivery phases

### Phase 0 - Repository and project baseline

**Goal:** Establish a clean, reproducible starting point before feature work.

1. Inspect repository contents and existing environment artifacts; identify any accidental generated files.
2. Decide project root and package layout, using the proposed `src/webcam_filter_app/` organization unless the repository already establishes a different convention.
3. Add/confirm version control hygiene: ignore virtual environments, caches, build outputs, and any local image/video files.
4. Choose supported Python version and project/dependency format (`pyproject.toml` preferred, or a pinned requirements file if that fits the learning context).
5. Add a minimal README skeleton describing project purpose and current status.

**Deliverables:** repository layout, ignore rules, dependency definition, README skeleton.

**Exit criteria:** a clean environment can be created from documented dependency metadata; no webcam footage or environment directory is tracked.

### Phase 1 - Product agreement and acceptance criteria

**Goal:** Resolve scope and release assumptions before coding.

1. Confirm the primary user and v1 outcome stated above.
2. Agree on target OS/version, Python version, and the actual camera/hardware used for release checks.
3. Confirm the single-camera, single-preview experience and the four initial states: original, grayscale, shape overlay, and text overlay.
4. Define the keyboard map, on-screen hint, and quit behavior.
5. Define a measurable responsiveness check on target hardware. Measure first; do not promise a frame rate before evidence.
6. Adopt privacy acceptance criteria: frames stay in process memory; app does not record, save, upload, transmit, or log image content.
7. Capture open questions and decisions in the log at the end of this plan.

**Deliverables:** concise product brief, prioritized v1 requirements, platform/hardware support statement draft, acceptance checklist.

**Exit criteria:** no unresolved question changes the v1 flow or creates a hidden data-handling requirement.

### Phase 2 - Design and implementation contracts

**Goal:** Agree on module boundaries and failure behavior.

1. Create the package skeleton and entry point.
2. Specify camera adapter methods and their return/error semantics (camera opened, frame available/valid, release safe to call more than once).
3. Specify effect identifiers and the frame processor contract (valid input, supported effect, output dimensions/type/channels, input mutation policy).
4. Specify display/input adapter operations, including how a close-window event is detected on chosen platforms.
5. Define the app loop order: read -> validate -> process -> display -> poll input -> repeat.
6. Define one shutdown path and cleanup order. Ensure `finally`-style cleanup covers quit, failed reads, and unexpected exceptions.
7. Sketch UI states: startup, active preview with visible effect/control hint, camera error, and shutdown.
8. Decide what diagnostic information is useful and safe; keep details in local operational logs only, without image data.

**Deliverables:** module skeleton, brief design note/diagram if needed, function contracts, UI state sketch, error mapping.

**Exit criteria:** each module has one clear owner responsibility and can be implemented/tested without mixing camera, effect, and window concerns.

### Phase 3 - Camera feasibility spike

**Goal:** Validate the riskiest hardware and platform assumptions early.

1. Build a temporary or minimal vertical slice that opens the default camera and displays unmodified frames.
2. Check camera-open failure and frame-read failure paths.
3. Verify quit key and window close both release the device and close the preview.
4. Test camera permission behavior and relaunch after normal exit on each target OS.
5. Record actual resolution/latency observations and any hardware or OpenCV window quirks; do not retain sample footage.
6. Decide whether source-based execution is enough or packaging needs a later experiment.

**Deliverables:** spike notes, confirmed/revised platform assumptions, reusable camera/display integration insights.

**Exit criteria:** at least one actual target machine can preview and exit cleanly; known limitations are recorded. If it fails, resolve platform/camera strategy before building effects.

### Phase 4 - Core frame effects

**Goal:** Implement effect transformations as small, isolated functions.

1. Implement original/pass-through behavior with a clear copy policy.
2. Implement grayscale conversion and ensure output can be displayed consistently with other effects.
3. Implement a simple geometric overlay, positioned to avoid covering the central subject where practical.
4. Implement text overlay with readable contrast and stable placement.
5. Define behavior for invalid frames and unsupported effect identifiers; fail clearly or preserve current selection without crashing.
6. Use synthetic arrays for automated tests; do not use real webcam footage as a fixture.
7. Verify array shape, dtype, channel layout, dimensions, and whether the original input was mutated.

**Deliverables:** `effects.py`, unit tests for each effect and edge cases.

**Exit criteria:** effects work on synthetic frames without a camera/window; outputs are displayable and documented; invalid inputs cannot silently propagate.

### Phase 5 - Application loop and live integration

**Goal:** Connect the adapters and effects into the complete v1 flow.

1. Implement camera adapter open/read/status/release behavior.
2. Implement display adapter preview, key polling, window-close event support, and destroy behavior.
3. Implement app startup: initialize display, attempt camera open, verify success, then enter the loop; on failure, give a concise explanation and clean up.
4. Implement the loop with explicit frame validity checks before processing.
5. Connect selected-effect state to processor and key input; unsupported key input leaves the current effect unchanged.
6. Add an unobtrusive high-contrast effect/control hint; do not communicate state through color alone.
7. Route keyboard quit, window close, failed read, handled exception, and unexpected exception through guaranteed cleanup.
8. Add safe user-facing errors and useful non-sensitive diagnostics. Keep frame content out of all logs and error artifacts.

**Deliverables:** working application flow, visible controls, cleanup/error behavior, app-flow tests using fakes.

**Exit criteria:** the app works end-to-end with fake/controlled frames and on the target camera; all exit paths release the camera and close windows.

### Phase 6 - Quality, usability, privacy, and compatibility pass

**Goal:** Verify behavior beyond the happy path.

1. Run unit tests for frame effects and component/app-flow tests with fake cameras.
2. Manually test each supported OS: permission granted/denied, camera missing/busy/disconnected, invalid/failed read, each effect shortcut, quit shortcut, window close, and relaunch.
3. Measure preview responsiveness on target hardware and record the method/result. Optimize only where measurement points to avoidable work.
4. Review UI for readable controls, clear active-effect indication, high contrast, and an obvious exit.
5. Review data paths and dependencies: no frames written, no network usage, no frame logging, no unnecessary permissions; list and pin dependencies tested.
6. Review failure messages and issue-report guidance for safe diagnostics and redaction.
7. Capture actual supported platforms/cameras and known limitations. Remove unsupported claims.

**Deliverables:** test results, manual test checklist, usability/compatibility findings, privacy and dependency review notes.

**Exit criteria:** automated checks pass; manual acceptance checklist passes on every declared supported platform; any open defect is documented and release-blocking issues are fixed.

### Phase 7 - Documentation and release readiness

**Goal:** Make the app repeatable for a new user.

1. Complete README prerequisites and tested platform details.
2. Document environment setup, dependency installation, launch instructions, all controls, privacy behavior, and camera troubleshooting.
3. Provide expected error guidance for permissions, busy/missing camera, and unsupported hardware.
4. Verify setup from a clean environment following only the README.
5. Choose a version identifier and release notes including known limitations.
6. If a standalone executable is required, evaluate packaging now; test permissions, OpenCV window behavior, and installation separately on each target OS. Do not let packaging replace source-based verification.
7. Confirm no generated environment, caches, or personal media enter the release/repository.

**Deliverables:** complete README, reproducible dependency setup, clean-install verification, versioned release or repeatable demonstration.

**Exit criteria:** a first-time user can install/run and complete the main journey; release checks and platform claims are traceable to actual tests.

### Phase 8 - Handoff and ongoing ownership

**Goal:** Leave a maintainable application, not just a demo.

1. Identify repository maintainer, issue-report route, and dependency update owner/cadence.
2. Publish or hand off the versioned build/source with known limitations and support statement.
3. Ask issue reporters for app version, OS, Python/package version, camera model if known, steps, and error text; do not request webcam footage/screenshots by default.
4. Reproduce reports first with synthetic frames or another non-sensitive setup; request additional diagnostic detail only when necessary and explain/redact it.
5. Track feature requests separately from v1 defects. Revisit architecture if controls outgrow a few shortcuts or if camera selection/resolution becomes needed.
6. Require new product, consent, data retention, security, and privacy decisions before any recording, screenshot, sharing, analytics, or cloud behavior.

**Deliverables:** ownership note, issue template/guidance, maintenance backlog, recorded future decisions.

**Exit criteria:** another person knows how to run the app, report an issue safely, and identify who maintains it.

## Requirements traceability

| Requirement | Planned implementation | Verification |
| --- | --- | --- |
| FR-1: opens default/selected camera and previews live video | Phases 3 and 5 | target-machine manual integration check |
| FR-2: switches supported effects | Phases 4 and 5 | effect unit tests plus live shortcut checks |
| FR-3: quits by shortcut/window close | Phases 3 and 5 | both routes manually exercised |
| FR-4: useful camera/frame failure message | Phases 2, 5, and 6 | fake failure-path tests plus manual missing/busy camera check |
| FR-5: releases camera/windows on exit and handled errors | Phases 2, 5, and 6 | cleanup assertions with fakes plus manual relaunch check |
| Privacy: no saving/transmission | All phases; explicit review in Phase 6 | code/config/dependency review; no recording/network features in v1 |
| Responsiveness: acceptable on target hardware | Phases 1, 3, and 6 | measured and recorded on declared hardware |

## Version 1 release acceptance checklist

- [ ] A first-time user can follow the README to install/run.
- [ ] The preview starts when permission and hardware are available.
- [ ] Original, grayscale, shape, and text effects can each be selected and behave as described.
- [ ] Controls and exit instructions are visible or documented.
- [ ] Missing/busy camera and failed frame reads produce understandable behavior without invalid-frame crashes.
- [ ] Keyboard quit and window close both exit through cleanup; camera can be opened again after exit.
- [ ] No video/frame is written to disk, sent over a network, or included in logs/diagnostics.
- [ ] Automated tests pass and manual checks cover every claimed platform.
- [ ] Tested dependency versions, version identifier, supported platform/hardware, and known limitations are recorded.
- [ ] Release has an owner and a safe issue-report path.

## Suggested implementation order

Follow the phases in order through the camera spike. After the spike, effect work and documentation scaffolding can proceed independently, but integrate only after their contracts are agreed. Do not defer cleanup and failure behavior to a final polish pass; implement and verify it with the initial camera loop.

## Decision log

Update this table during Phase 1/2. Use `Open` until supported by an explicit decision or evidence.

| Decision | Status | Decision / evidence |
| --- | --- | --- |
| Supported operating systems and minimum versions | Open | Development ran on macOS 27.0 ARM64; physical camera and GUI flow still require manual verification before claiming support. |
| Python version and tested OpenCV/dependency versions | Selected for initial implementation | Python >=3.12; development venv is Python 3.14.7 with OpenCV 5.0.0.93 and NumPy 2.5.3. Automated tests pass in this environment. |
| Target camera models/hardware | Open | No physical camera integration check recorded yet. |
| Default camera index vs camera selection | Selected for v1 | Use default camera index 0; camera selection remains out of scope. |
| Effect and quit shortcuts | Selected for v1 | 1 original, 2 grayscale, 3 shape, 4 text, Q/q or Escape to quit. |
| Source execution vs standalone packaging | Selected for v1 | Source execution and editable installation; no standalone packaging in v1. |
| Measured responsiveness acceptance | Open | Measure on chosen target hardware before setting a performance target. |
| Maintainer, issue route, dependency cadence | Open | Assign before release. |

## Implementation status (2026-10-02)

- Implemented the package structure, camera/display adapters, frame validation/effects, application loop, CLI entry point, pinned dependency metadata, README, and synthetic-frame/fake-adapter tests.
- On macOS, the camera adapter explicitly selects AVFoundation and logs its selected backend. The preview shows a warning after 30 consecutive frames with no sampled nonzero pixels; this does not identify a unique cause.
- Ran `./venv/bin/python -m unittest discover -s tests -v`: 10 tests passed.
- The app has not yet been manually opened against a physical camera. OS permission behavior, window-close behavior, camera disconnection, and responsiveness remain release checks from Phases 3 and 6.
- No source-based clean-install check has been recorded; editable installation succeeded in the development venv.

## Source

Derived from `Webcam_Filter_App_System_Architecture.pdf` in this directory. This plan operationalizes that guide and does not expand the app's version 1 scope.
