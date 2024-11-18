import os
HOME = os.getcwd()

from IPython import display
display.clear_output()

import ultralytics
ultralytics.checks()

from IPython import display
display.clear_output()

import supervision as sv

from supervision.assets import download_assets, VideoAssets

from ultralytics import YOLO

model = YOLO("yolov8x.pt")

SOURCE_VIDEO_PATH = "yolo_testvids/vid3.mp4"
CLASS_NAMES_DICT = model.model.names

SELECTED_CLASS_NAMES = ['car', 'bus', 'truck']

SELECTED_CLASS_IDS = [
    {value: key for key, value in CLASS_NAMES_DICT.items()}[class_name]
    for class_name
    in SELECTED_CLASS_NAMES
]

import supervision as sv
import numpy as np

generator = sv.get_video_frames_generator(SOURCE_VIDEO_PATH)
# create instance of BoxAnnotator and LabelAnnotator
box_annotator = sv.BoxAnnotator(thickness=4)
label_annotator = sv.LabelAnnotator(text_thickness=2, text_scale=1.5, text_color=sv.Color.BLACK)
# acquire first video frame
iterator = iter(generator)
frame = next(iterator)
# model prediction on single frame and conversion to supervision Detections
results = model(frame, verbose=False)[0]

# convert to Detections
detections = sv.Detections.from_ultralytics(results)
# only consider class id from selected_classes define above
detections = detections[np.isin(detections.class_id, SELECTED_CLASS_IDS)]

# format custom labels
labels = [
    f"{CLASS_NAMES_DICT[class_id]} {confidence:0.2f}"
    for confidence, class_id in zip(detections.confidence, detections.class_id)
]

# annotate and display frame
annotated_frame = frame.copy()
annotated_frame = box_annotator.annotate(
    scene=annotated_frame, detections=detections)
annotated_frame = label_annotator.annotate(
    scene=annotated_frame, detections=detections, labels=labels)

# %matplotlib inline
sv.plot_image(annotated_frame, (16, 16))


# settings
LINE_START = sv.Point(0 + 50, 1500)
LINE_END = sv.Point(3840 - 50, 1500)

TARGET_VIDEO_PATH = f"{HOME}/result.mp4"

sv.VideoInfo.from_video_path(SOURCE_VIDEO_PATH)

import numpy as np

# Define global counters for in and out
in_count = 0
out_count = 0

# Create BYTETracker instance
byte_tracker = sv.ByteTrack(
    track_activation_threshold=0.25,
    lost_track_buffer=30,
    minimum_matching_threshold=0.8,
    frame_rate=30,
    minimum_consecutive_frames=3
)
byte_tracker.reset()

# Create VideoInfo instance
video_info = sv.VideoInfo.from_video_path(SOURCE_VIDEO_PATH)

# Create frame generator
generator = sv.get_video_frames_generator(SOURCE_VIDEO_PATH)

# Create LineZone instance, previously called LineCounter
line_zone = sv.LineZone(start=LINE_START, end=LINE_END)

# Create instances of annotators
box_annotator = sv.BoxAnnotator(thickness=4)
label_annotator = sv.LabelAnnotator(text_thickness=2, text_scale=1.5, text_color=sv.Color.BLACK)
trace_annotator = sv.TraceAnnotator(thickness=4, trace_length=50)
line_zone_annotator = sv.LineZoneAnnotator(thickness=4, text_thickness=4, text_scale=2)

# Callback function for video processing
def callback(frame: np.ndarray, index: int) -> np.ndarray:
    global in_count, out_count  # Reference the global variables

    # Model prediction on single frame and conversion to supervision Detections
    results = model(frame, verbose=False)[0]
    detections = sv.Detections.from_ultralytics(results)

    # Only consider selected class ids
    detections = detections[np.isin(detections.class_id, SELECTED_CLASS_IDS)]

    # Track detections
    detections = byte_tracker.update_with_detections(detections)
    labels = [
        f"#{tracker_id} {model.model.names[class_id]} {confidence:0.2f}"
        for confidence, class_id, tracker_id
        in zip(detections.confidence, detections.class_id, detections.tracker_id)
    ]

    # Annotate frame
    annotated_frame = frame.copy()
    annotated_frame = trace_annotator.annotate(scene=annotated_frame, detections=detections)
    annotated_frame = box_annotator.annotate(scene=annotated_frame, detections=detections)
    annotated_frame = label_annotator.annotate(scene=annotated_frame, detections=detections, labels=labels)

    # Update line zone and increment counters
    previous_in_count, previous_out_count = line_zone.in_count, line_zone.out_count
    line_zone.trigger(detections)

    # Check if counts have changed and update global counts
    if line_zone.in_count > previous_in_count:
        in_count += line_zone.in_count - previous_in_count
        print("in:",in_count)
    if line_zone.out_count > previous_out_count:
        out_count += line_zone.out_count - previous_out_count
        print("out",out_count)

    # Annotate frame with line zone results
    return line_zone_annotator.annotate(annotated_frame, line_counter=line_zone)

sv.process_video(
    source_path=SOURCE_VIDEO_PATH,
    target_path=TARGET_VIDEO_PATH,
    callback=callback
)

print(f"Total In Count: {in_count}")
print(f"Total Out Count: {out_count}")