# From Webcam Filters to Object Detection

## Student Notes

**Author:** Shashank Jha  
**Project:** Webcam Filter App  
**Version:** 1.0  
**Prepared:** 4 October 2026

---

## How to use these notes

These notes explain the Webcam Filter App as it exists today, then build a bridge to object detection. They are intended for students who know basic Python and want to connect application code to computer vision and machine learning ideas.

The first part describes deterministic image processing: a camera supplies frames and OpenCV changes or annotates those frames. The second part introduces object detection, which uses a trained model to predict what objects appear and where they are. The current app does **not** contain a neural network or perform object detection. Detection is a next learning step, not a feature hidden behind one of the current keys.

The code and commands in this document are teaching examples. Use the repository README for the exact setup of the current app. For APIs that evolve, use the linked official documentation as the final reference.

## Learning objectives

After working through the notes, a student should be able to:

1. Describe how a webcam frame moves through this application.
2. Explain pixels, image arrays, BGR channels, grayscale conversion, overlays, and frame validation.
3. Find the camera, effect, display, configuration, and lifecycle responsibilities in the source tree.
4. Explain the difference between image classification, object detection, segmentation, and tracking.
5. Read a bounding box, class ID, confidence score, and IoU value.
6. Run a pretrained detector on a permitted local image and inspect its results.
7. Describe how labeled data, training, validation, and evaluation fit together.
8. Identify privacy, licensing, performance, and reliability issues before extending a live-camera application.

## 1. What the application does

The app is a small local desktop program. It opens one camera, reads one frame at a time, applies the selected visual effect, shows the result in an OpenCV window, and polls keyboard controls. Processing stays in the app's memory.

```text
Camera
  -> capture adapter
  -> validate one frame
  -> selected effect
  -> display plus controls
  -> read key or window-close action
  -> repeat, or clean up and exit
```

The v1 effects are:

- **Original:** show the captured color frame.
- **Grayscale:** convert the color image to a one-channel intensity image.
- **Shape:** draw one circle over a copy of the frame.
- **Text:** draw a short text label over a copy of the frame.

The `3` key selects the Shape effect. In the current implementation that effect is specifically a circle. It is a drawing demonstration; it does not locate an object or understand the camera scene.

### Controls

| Key | Action |
| --- | --- |
| `1` | Original color |
| `2` | Grayscale |
| `3` | Circle overlay |
| `4` | Text overlay |
| `Q` or `q` | Quit |
| `Esc` | Quit |
| Preview window close control | Quit and release resources |

## 2. The architecture and source code

The source package is `src/webcam_filter_app/`. Each module owns one part of the application so students can understand and test it without mixing all behavior into one large function. The companion [architecture guide](Webcam_Filter_App_System_Architecture.pdf), [development plan](DEVELOPMENT_PLAN.md), and [README](README.md) give the project-specific design, delivery sequence, and setup steps.

| Module | Responsibility |
| --- | --- |
| `main.py` | Starts the app and converts known or unexpected failures into process exit messages. |
| `app.py` | Coordinates startup, the frame loop, effect selection, errors, and cleanup. |
| `camera.py` | Opens, reads, reports, and releases a camera capture handle. |
| `effects.py` | Validates image arrays and applies deterministic frame transformations. |
| `display.py` | Creates the preview window, draws the control/status strip, polls keys, and closes the window. |
| `config.py` | Defines validated defaults for camera index, shortcuts, and window name. |

### 2.1 `main.py`: the program entry point

Python executes the `main()` function when the module is launched with:

```bash
./venv/bin/python -m webcam_filter_app.main
```

The entry point constructs `App`, calls `run()`, and handles `CameraError` separately from unexpected exceptions. A camera error gets a short message. An unexpected error gets a diagnostic traceback in the launching terminal and a brief user-facing message.

This keeps command-line startup concerns separate from camera and image logic. The `if __name__ == "__main__"` guard also lets Python import the module without starting the camera as a side effect.

### 2.2 `camera.py`: owning the device resource

The `Camera` class wraps `cv2.VideoCapture`. It opens camera index `0` by default. On macOS it asks OpenCV to use the AVFoundation backend; on other systems it asks for OpenCV's default backend.

Important ideas:

- `isOpened()` checks whether OpenCV opened a capture device. It does not prove that the pixels contain a useful picture.
- `read()` returns a success flag and a frame. A failed read returns no frame; the rest of the app must not process it.
- `release()` gives the device back to the operating system. It is safe to call during cleanup even if the camera was never successfully opened.
- The adapter logs the camera index and selected backend. It does not log frame pixels.

Camera devices are resources, like open files. Failing to release them can leave a camera busy or prevent a later app launch from using it.

### 2.3 `effects.py`: image arrays and transformations

OpenCV frames are NumPy arrays. A common color frame has shape:

```text
(height, width, 3)
```

The first coordinate is a row (`y`), the second is a column (`x`), and the third selects a color channel. OpenCV conventionally stores color images in **BGR** order: blue, green, then red. The data type `uint8` stores each channel as an integer from 0 through 255.

The app's `validate_frame()` checks that a frame is:

- a NumPy array;
- an 8-bit unsigned array (`uint8`);
- a three-channel color image;
- within the app's maximum image edge and pixel-count limits.

These checks catch failed or unexpected input before it reaches OpenCV drawing and conversion functions. The limits are defensive bounds for this project, not universal limits for every camera.

`apply_effect(frame, effect)` first validates the input and the requested effect. Each effect is deterministic: the same frame and effect produce the same result.

**Original** returns a copy. **Grayscale** uses `cv2.cvtColor` with `cv2.COLOR_BGR2GRAY`. Conceptually, each gray intensity is a weighted combination of the color channels; green contributes most to perceived brightness, while blue contributes less. The output shape is `(height, width)`, because it has one intensity value per pixel instead of three color values.

**Shape** copies the source frame and calls `cv2.circle`. It calculates the center from the image width and height and sets the circle radius from the smaller dimension. **Text** copies the source frame and calls `cv2.putText`. Copying means the source frame remains unchanged while the output is drawn on.

The actual operations are small and explicit:

```python
gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

output = frame.copy()
cv2.circle(output, center, radius, color, thickness=4)
cv2.putText(output, "Webcam Filter", origin, font, scale, color, thickness=2)
```

Drawing and color conversion touch some or all of the pixels. Their work grows with image dimensions, so resolution affects CPU time and memory. A copied 1920 by 1080 BGR frame alone contains about 6.2 million bytes, before any internal temporary arrays.

### 2.4 `display.py`: showing the result and handling input

`Display` owns one OpenCV window. `show_frame()` draws a high-contrast control strip on the processed output and calls `cv2.imshow()`. `read_key()` calls `cv2.waitKey(1)` to process GUI events and obtain keyboard input. OpenCV's GUI loop needs a key-polling call to keep the window responsive.

The display can also show a diagnostic after it observes 30 consecutive frames whose sampled pixels are all zero. To keep that check inexpensive, the app samples a small grid rather than scanning every pixel. The message is a clue to check the permission, lens cover, or selected camera; it is not proof of which problem occurred. A genuinely black scene can trigger the same warning.

### 2.5 `config.py`: validated controls

`AppConfig` keeps defaults in one place. Camera index `0` is a simple v1 choice. It does not enumerate or let the user select cameras. The effect keys map to effect identifiers; the quit keys are `q`, `Q`, and Escape.

Validation prevents negative or non-integer camera indexes, an empty window name, and shortcut conflicts. The shortcut mapping is wrapped as read-only data so another part of the program cannot accidentally change it while the app is running.

### 2.6 `app.py`: the frame loop

The important order in `App.run()` is:

1. Create the display window.
2. Open the camera; show a concise startup error if it cannot be opened.
3. Check that the display is still open.
4. Read one frame; stop if capture failed.
5. Validate the frame before processing.
6. Sample for a persistent all-zero image and prepare a warning if needed.
7. Apply the selected effect and display the result.
8. Poll keys and update the selected effect, or exit on a quit key.
9. In a `finally` block, release the camera and close the display.

The `finally` block is important: it runs whether the user quits normally or an error interrupts the loop. The loop stores only the current frame and processed output; it does not build a growing list of past frames.

### 2.7 Automated tests

The app's tests use small synthetic NumPy arrays and fake camera/display adapters. They check such behavior as output frame shape and data type, invalid-frame rejection, keyboard selection, failed reads, camera-open failure, cleanup, and the black-frame warning.

They do not need to turn on a physical webcam. That makes them repeatable and avoids putting personal camera images in the test suite.

## 3. How to get started with the current app

Use the project virtual environment for installing packages, running the app, and running its tests. From the `webcam-filter-app` directory:

```bash
python3 -m venv venv
./venv/bin/python -m pip install --upgrade pip
./venv/bin/python -m pip install -e .
./venv/bin/python -m webcam_filter_app.main
```

The app pins OpenCV and NumPy in `pyproject.toml`. You need a camera and operating-system permission to use it. Camera support must be confirmed on real hardware; successful package installation alone does not demonstrate that a camera works.

Run automated checks with:

```bash
./venv/bin/python -m unittest discover -s tests -v
```

On Windows PowerShell, activate the same environment and use `venv\\Scripts\\python.exe` instead of `./venv/bin/python`.

## 4. From image processing to object detection

### 4.1 What is object detection?

Object detection takes an image and returns zero or more detections. A typical detection contains:

1. **Class:** what category the model predicts, such as `cup` or `bicycle`.
2. **Bounding box:** where the object is in the image.
3. **Confidence score:** the model's score for this predicted detection.

For example, a detector might return: “cup, score 0.91, box from pixel `(120, 60)` to `(260, 310)`.” It can return several boxes for one image.

Object detection is different from the current circle overlay. The circle uses a hand-calculated image center and radius. A detector examines learned visual patterns and predicts boxes and classes based on its training.

### 4.2 Related computer vision tasks

| Task | Typical output | Example question |
| --- | --- | --- |
| Image classification | One or more labels for a whole image | Is this image a cat? |
| Object detection | A class and rectangle for each object | Where are the cats and dogs? |
| Instance segmentation | A separate pixel mask per object | Which exact pixels belong to this cat? |
| Semantic segmentation | A class for each pixel, without separating same-class instances | Which pixels are road, building, or sky? |
| Object tracking | A consistent ID for detections across video frames | Is this the same person seen in the previous frame? |

Detection does not automatically recognize a person's identity. Face recognition or identity inference is a different and sensitive capability, and it is outside this project's v1 scope.

### 4.3 A detector's broad processing pipeline

Modern detector internals vary, but a useful high-level model is:

```text
Image
  -> resize/prepare tensor
  -> neural network extracts visual features
  -> predict candidate classes and box coordinates
  -> filter low-confidence candidates
  -> remove duplicate overlapping boxes
  -> return detections in original image coordinates
```

The preprocessing stage may resize an image and add padding so its dimensions fit a model. The model performs inference: it uses learned weights to calculate outputs without updating those weights. Post-processing turns raw model outputs into the boxes, classes, and scores used by the application.

### 4.4 Neural-network intuition

A convolutional neural network applies learned filters to local image regions. Early layers often respond to simple patterns such as edges and color changes. Deeper layers combine those patterns into more complex visual features. A detector uses these learned features to predict both **what** is present and **where** it is.

During training, an image and its labeled boxes are passed through the network. A loss function measures errors in localization and class prediction. An optimizer uses gradients to update model weights, gradually reducing the training loss. During inference, weights stay fixed and the model calculates predictions for new input.

Many detector families are described as **one-stage** or **two-stage**. A one-stage design predicts candidates directly in a detector pass; YOLO is a well-known family built around this style of end-to-end prediction. A two-stage design first proposes regions and then classifies/refines those regions; Faster R-CNN is a landmark example. This is a conceptual comparison: current models differ in architecture and implementation, and the fastest option depends on the machine, model size, and input resolution. The original [YOLO paper](https://arxiv.org/abs/1506.02640) and [Faster R-CNN paper](https://arxiv.org/abs/1506.01497) describe influential early designs.

### 4.5 Bounding boxes and coordinates

This project and common detector APIs use image coordinates where `(0, 0)` is the top-left. A predicted `xyxy` box contains:

```text
x1, y1 = top-left corner
x2, y2 = bottom-right corner
```

The width is `x2 - x1`; the height is `y2 - y1`. Coordinates may use pixels or normalized values, so always check the API's format before drawing or comparing boxes.

For a labeled box with pixel coordinates and an image of width `W` and height `H`, normalized YOLO `xywh` values are:

```text
x_center = (x1 + x2) / (2 * W)
y_center = (y1 + y2) / (2 * H)
box_width = (x2 - x1) / W
box_height = (y2 - y1) / H
```

All four normalized values should be between 0 and 1. The class ID is a zero-based integer that refers to a class-name list or map.

### 4.6 Confidence threshold and duplicate boxes

A confidence threshold controls which low-scoring predictions are returned. Raising the threshold usually removes more weak candidates, which may reduce false alarms but can also miss real objects. Lowering it may find more objects but can show more false positives. A confidence score is a model output, not a guarantee that the prediction is correct or a universally calibrated probability.

Detectors can predict several highly overlapping boxes for one object. **Intersection over Union (IoU)** measures overlap between two boxes:

```text
IoU = area of intersection / area of union
```

IoU ranges from 0 (no overlap) to 1 (identical boxes). Non-Maximum Suppression (NMS) commonly keeps a strong candidate and removes lower-scoring candidates that overlap it too much. The confidence threshold and the NMS IoU threshold solve different problems: one filters low scores; the other filters duplicate boxes.

NMS can have quadratic work in the number of candidates in a simple implementation, so modern detectors limit or sort candidates. For app development, prefer the model library's supported post-processing over writing an unbounded pairwise comparison over every possible box.

## 5. First object-detection exercise: use a pretrained model

Start with a still image before using a webcam. This helps separate model/setup errors from camera permission, camera selection, and live-window problems.

### 5.1 Use a separate virtual environment

Object-detection libraries add large machine-learning dependencies and model files. Keep the current app environment small until detection becomes a planned app feature. From the project directory, create a separate learning environment:

```bash
python3 -m venv .venv-detection
source .venv-detection/bin/activate
python -m pip install --upgrade pip
python -m pip install -U ultralytics
```

On Windows PowerShell, activate with `.venv-detection\\Scripts\\Activate.ps1`. Check the current [Ultralytics installation guide](https://docs.ultralytics.com/quickstart) for supported platforms and setup details. The first installation can download packages; the first model load can download model weights. That means the learning environment needs network access at setup time. The camera-filter app itself does not need a network connection at runtime.

### 5.2 Run a local image through the model

Put a lawful, non-sensitive sample image at `local_media/sample.jpg`. Do not use a person's image without permission. `local_media/` is ignored by Git in this project so personal or local images are not accidentally included in commits.

Current Ultralytics documentation demonstrates the small pretrained `yolo26n.pt` detector. The `n` model variant is intended to be the lighter model in that family; actual speed and accuracy still need measurement on the student's machine.

```python
from ultralytics import YOLO


def main() -> None:
    # Load weights once, not once per image or frame.
    model = YOLO("yolo26n.pt")

    # Run inference on one local image. No output file is requested here.
    results = model.predict(
        source="local_media/sample.jpg",
        imgsz=640,
        conf=0.25,
        save=False,
        verbose=False,
    )

    for result in results:
        # Each box contains pixel corners, confidence, and a class ID.
        for box in result.boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().tolist()
            confidence = float(box.conf[0].item())
            class_id = int(box.cls[0].item())
            class_name = result.names[class_id]
            print(
                f"{class_name}: {confidence:.2f} "
                f"box=({x1:.0f}, {y1:.0f}, {x2:.0f}, {y2:.0f})"
            )

        # plot() returns an annotated BGR NumPy image.
        annotated_bgr = result.plot()
        print("Annotated preview shape:", annotated_bgr.shape)


if __name__ == "__main__":
    main()
```

Save the example as `detect_image.py` and run it from the active detection environment:

```bash
python detect_image.py
```

The model returns a result for each input image. `result.boxes.xyxy` holds pixel box coordinates, `result.boxes.conf` holds confidence scores, and `result.boxes.cls` holds numeric class IDs. `result.names` maps each class ID to a readable name. `result.plot()` creates an annotated image in memory; this example does not save it. See the official [predict guide](https://docs.ultralytics.com/modes/predict) for current API details.

### 5.3 What the example does not do

- It does not train a model; it runs already-trained weights.
- It only recognizes classes represented by the selected pretrained model.
- It does not promise a real-time speed on every computer.
- It does not save the input or annotated image.
- It does not integrate a detector into the webcam app.

If a desired object class is not in the pretrained model's class list, the next step is to prepare a suitable labeled dataset and fine-tune a model. Fine-tuning changes learned weights using task-specific examples; it is not just changing the displayed class name.

## 6. Preparing a custom object-detection dataset

### 6.1 Decide what counts as an object

Before collecting data, write down:

- the classes you want to detect;
- what qualifies as an instance of each class;
- whether partially hidden objects are labeled;
- how tightly boxes should follow visible objects;
- how to handle tiny, blurry, truncated, or ambiguous objects.

Consistent labeling matters. If two annotators draw very different boxes for the same object, the model receives conflicting examples.

### 6.2 Capture representative examples

A useful dataset resembles the images the model will see after training. Include different examples of lighting, angle, distance, backgrounds, object sizes, and occlusion. Add images where the target class is absent so evaluation can reveal false positives. Do not let nearly identical neighboring video frames leak across the training and validation sets; otherwise validation can look better than real-world performance.

Students should use open, appropriately licensed datasets or images captured with informed permission. Avoid uploading private webcam frames to annotation or training services without approval. Treat images and trained model weights as project data and document where they came from. Check image and annotation licenses as well as model licenses.

### 6.3 Split and label the data

Separate examples into:

- **Training split:** examples used to update model weights.
- **Validation split:** examples used while selecting settings and comparing model versions.
- **Test split:** held-back examples used for the final evaluation.

Do not tune repeatedly against the test split. Once students use test results to make design decisions, the test set is no longer an independent final check.

In the Ultralytics YOLO label format, each image has a same-named `.txt` file. Each object row is:

```text
class_id x_center y_center width height
```

Coordinates are normalized `xywh` values from 0 to 1 and class IDs start at 0. For example, the following means a class-1 object centered halfway across the image and one-quarter down, with half the image width and one-half the image height:

```text
1 0.500 0.250 0.500 0.500
```

A simple dataset layout is:

```text
my_dataset/
  images/
    train/
    val/
    test/
  labels/
    train/
    val/
    test/
  data.yaml
```

The YAML file points to the splits and gives each integer class ID a name:

```yaml
path: my_dataset
train: images/train
val: images/val
test: images/test
names:
  0: bottle
  1: cup
```

The official [Ultralytics detection dataset guide](https://docs.ultralytics.com/datasets/detect) describes its current formats and directory conventions. Check the installed version's guide before preparing a large dataset.

## 7. Training and evaluating a detector

### 7.1 Transfer learning

Training from random weights requires substantial data and compute. A common learning path is **transfer learning**: begin from weights that already learned general image features, then train or fine-tune them for the new classes. This often reaches a useful starting point with less task-specific data than training from scratch, though results depend on the similarity between the pretraining and target domains.

An Ultralytics-style training example is:

```python
from ultralytics import YOLO

model = YOLO("yolo26n.pt")
train_results = model.train(
    data="my_dataset/data.yaml",
    epochs=50,
    imgsz=640,
)
```

Training changes the model weights. Keep the training data, label map, package version, configuration, model weights, and evaluation results associated with each experiment so results can be reproduced.

### 7.2 Metrics

No single metric explains every failure. Review the validation images and the per-class results as well as summary values.

- **True positive (TP):** a predicted box matches a labeled object under the evaluation rules.
- **False positive (FP):** the model reports an object that should not count as a match.
- **False negative (FN):** a labeled object is missed.
- **Precision:** `TP / (TP + FP)`. Of the predictions made, how many were correct?
- **Recall:** `TP / (TP + FN)`. Of the real labeled objects, how many were found?
- **IoU:** overlap between a prediction and a labeled box; evaluation uses an IoU threshold to decide whether a box is a match.
- **Average Precision (AP):** summarizes a class's precision-recall tradeoff across confidence thresholds, commonly as area under its precision-recall curve.
- **mean Average Precision (mAP):** averages AP across classes, and often across IoU thresholds. `mAP@0.50` is more permissive about overlap than `mAP@0.50:0.95`.

The confidence threshold shifts the precision/recall balance at inference time. Select it using the costs of false alarms and missed objects in the intended task, not because one number is universally correct. [Ultralytics' metrics guide](https://docs.ultralytics.com/guides/yolo-performance-metrics) explains the current reported metrics.

### 7.3 Speed and accuracy are both part of quality

For a webcam app, measure end-to-end latency as well as model accuracy. Total time includes capture, image preparation, inference, drawing, and display. A model that is accurate but takes longer than the camera's frame interval can make the preview lag.

To keep a live app responsive:

1. Load the model once during startup; never reload it inside the frame loop.
2. Begin with a small model and a modest image size, then measure.
3. Process only the latest frame; do not queue an unlimited backlog of old frames.
4. If inference cannot run for every camera frame, skip some inference calls or use a bounded worker design after profiling.
5. Use streaming/generator behavior for long videos or collections so all results are not retained in memory. Ultralytics documents `stream=True` for memory-efficient result iteration.
6. Record preprocessing, inference, postprocessing, and full-loop latency separately when diagnosing lag.

Do not promise a frame rate before measuring on the target computer and camera.

## 8. How detection could fit this app later

Object detection deserves a later planned phase because it adds model dependencies, weights, latency, result handling, licensing, and new privacy considerations. A clean extension would keep responsibilities separated:

```text
Camera -> validate frame -> detector.py -> detections -> display boxes and labels
                                           |
                                  model loaded once at startup
```

A possible detector boundary could look like:

```python
class Detector:
    def load(self) -> None:
        """Load model weights once and report a useful failure if unavailable."""

    def predict(self, frame: np.ndarray) -> list[Detection]:
        """Return bounded, validated boxes, class IDs, and confidence values."""
```

`Detection` should be a simple data object containing coordinates, class ID/name, and confidence. The model library should stay behind this boundary so camera and display code do not depend on its internal tensor types.

Suggested extension sequence:

1. Run inference on a public or permitted still image in the separate environment.
2. Inspect boxes, class names, confidence, and false positives by hand.
3. Measure CPU and memory use on target hardware.
4. Add a `detector.py` adapter and synthetic/fake-result tests.
5. Integrate one frame at a time with an explicit bounded memory and latency policy.
6. Test camera permissions, device compatibility, errors, cleanup, and privacy manually.
7. Revisit dependency pins, supported Python/OS versions, licensing, and release documentation.

Do not add a model to the current v1 requirements until this extension is approved and planned. Keep inference local if that remains the product requirement. A model may download weights on its first use, so make this behavior explicit and then point inference to an approved local weights file. Do not save webcam frames or send them to a service by default.

## 9. Privacy, security, licensing, and responsible use

Webcam images can include faces, homes, documents, and bystanders. For this project's v1, frames are processed in memory and are not recorded, saved, uploaded, or sent to a server. A future detector sees the same sensitive pixels, even if it only returns boxes and class scores.

Before adding detection:

- explain what the model processes and whether model weights or services require network access;
- use local, permissioned images for development and testing;
- validate frame shape, data type, dimensions, box coordinates, class IDs, and confidence range before drawing;
- keep outputs and logs free of unnecessary personal information;
- cap resolution and candidate count to bound time and memory;
- check that drawing coordinates are within the image before using them;
- never run arbitrary model/config code from untrusted files;
- document the model source, version, license, and weight checksum/source where appropriate.

The Ultralytics package and model examples are governed by licensing terms that can impose source disclosure obligations. Review the current [Ultralytics license terms](https://www.ultralytics.com/license) before redistributing an application or model. The fact that an example runs is not a license review.

Detection scores are fallible. Performance can change with camera, lighting, distance, image quality, and population or object distribution. Do not use a classroom demonstration as the basis for consequential decisions about people.

## 10. Exercises and discussion prompts

### Source-reading exercises

1. Trace a frame from `Camera.read()` to `Display.show_frame()`. What prevents a failed read from reaching `apply_effect()`?
2. Run each current effect. Which functions allocate a new array? Why does that matter in a live loop?
3. Explain why a grayscale result has two dimensions while the original frame has three.
4. Locate the `finally` cleanup path. What would happen if the user closes the window instead of pressing `q`?
5. Create a synthetic `uint8` frame and verify that `apply_effect()` does not mutate it.

### Detection exercises

1. Run the pretrained model on a local, permitted image. Print each class name and confidence.
2. Draw a known `xyxy` box with OpenCV. Convert it to normalized YOLO `xywh`, then convert it back to pixels.
3. Pick three labeled and predicted box pairs and calculate IoU by hand.
4. Raise and lower the confidence threshold. Describe the change in false positives and missed objects.
5. Draw a duplicate detection over one object and explain what NMS is intended to remove.
6. Make a train/validation/test split. Explain why near-identical frames should not be distributed randomly across all three splits.
7. Compare a small and a larger model on the same target machine. Report latency and per-class quality; do not report FPS alone.
8. Propose how to keep the detector behind an adapter and how to test it without a webcam.

### Reflection questions

- What is one failure mode that a synthetic unit test can catch, and one that requires a real camera?
- When is a false positive more harmful than a false negative? When is the reverse true?
- What evidence would be needed before claiming that the detector works reliably in a new environment?
- Which data should never be included in logs, issue reports, or a public training dataset?
- What model, dependency, and dataset license questions arise before sharing the finished app?

## 11. Glossary

| Term | Meaning |
| --- | --- |
| Array shape | The size of each array dimension; an image commonly uses `(height, width, channels)`. |
| BGR / RGB | Channel orderings for blue, green, and red values. OpenCV uses BGR for many image APIs. |
| Bounding box | A rectangle represented by coordinates around an object. |
| Class ID | An integer that maps to a class name. |
| Confidence threshold | Minimum prediction score accepted by an inference call. |
| Frame | One image from a video stream. |
| Inference | Using trained model weights to produce predictions without training updates. |
| IoU | Intersection over Union, a ratio describing overlap between two boxes. |
| mAP | Mean Average Precision, an aggregate detection metric across classes and evaluation thresholds. |
| NMS | Non-Maximum Suppression, a post-processing method for reducing duplicate overlapping boxes. |
| Normalized coordinates | Coordinates scaled relative to image width/height, commonly in the interval 0 to 1. |
| Transfer learning | Starting from learned weights and adapting them to a related task or dataset. |
| Training / validation / test | Data splits for learning model weights, choosing settings, and final held-out evaluation. |

## 12. References and further reading

1. Project source of truth: `Webcam_Filter_App_System_Architecture.pdf` and `DEVELOPMENT_PLAN.md` in this directory.
2. [OpenCV 5 Python tutorials](https://docs.opencv.org/5.0/py_tutorials/py_tutorials.html) for image processing, GUI, video capture, and object-detection topics.
3. [OpenCV high-level GUI documentation](https://docs.opencv.org/5.0/main_modules/highgui.html) for `imshow`, event polling, and window behavior.
4. [Ultralytics object detection task guide](https://docs.ultralytics.com/tasks/detect) for current model use, training, validation, and prediction examples.
5. [Ultralytics prediction guide](https://docs.ultralytics.com/modes/predict) for input sources, result objects, boxes, and annotated outputs.
6. [Ultralytics detection dataset guide](https://docs.ultralytics.com/datasets/detect) for class maps and label formats.
7. [Ultralytics metrics guide](https://docs.ultralytics.com/guides/yolo-performance-metrics) for precision, recall, IoU, AP, and mAP.
8. Redmon et al., [You Only Look Once: Unified, Real-Time Object Detection](https://arxiv.org/abs/1506.02640), an influential single-stage detector paper.
9. Ren et al., [Faster R-CNN: Towards Real-Time Object Detection with Region Proposal Networks](https://arxiv.org/abs/1506.01497), an influential region-proposal detector paper.
10. [Ultralytics license information](https://www.ultralytics.com/license). Review current terms before redistribution or commercial use.

---

**End of student notes**
