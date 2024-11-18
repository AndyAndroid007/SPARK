# Cell 1: Importing required libraries
def yolo():
    import os
    HOME = os.getcwd()

    from IPython import display
    display.clear_output()

    import ultralytics
    ultralytics.checks()

    from IPython import display
    display.clear_output()

    import supervision as sv
    import numpy as np
    from ultralytics import YOLO

    # Setting up YOLO model
    model = YOLO("yolov8x.pt")
    SOURCE_VIDEO_PATH = "yolo_testvids/vid5.mp4"
    CLASS_NAMES_DICT = model.model.names

    # Selected classes
    SELECTED_CLASS_NAMES = ['car']
    SELECTED_CLASS_IDS = [
        {value: key for key, value in CLASS_NAMES_DICT.items()}[class_name]
        for class_name in SELECTED_CLASS_NAMES
    ]
    # print(f"Selected Class IDs: {SELECTED_CLASS_IDS}")

    # Cell 2: Visualize sample frames from the video
    generator = sv.get_video_frames_generator(SOURCE_VIDEO_PATH)

    # Display a few sample frames
    import matplotlib.pyplot as plt

    # iterator = iter(generator)
    # for i in range(3):  # Display first 3 frames for a quick visual check
    #     frame = next(iterator)
    #     plt.figure(figsize=(10, 10))
    #     plt.imshow(frame)
    #     plt.title(f"Frame {i+1}")
    #     plt.axis('off')
    #     plt.show()

    # Cell 3: Model Prediction on a Single Frame with Bounding Box Visualization
    # Create annotators
    box_annotator = sv.BoxAnnotator(thickness=4)
    label_annotator = sv.LabelAnnotator(text_thickness=2, text_scale=1.5, text_color=sv.Color.BLACK)

    # Get the first frame
    iterator = iter(generator)
    frame = next(iterator)

    # Model prediction  
    results = model(frame, verbose=False)[0]
    detections = sv.Detections.from_ultralytics(results)

    # Filter detections by selected classes
    detections = detections[np.isin(detections.class_id, SELECTED_CLASS_IDS)]

    # Format labels
    labels = [
        f"{CLASS_NAMES_DICT[class_id]} {confidence:0.2f}"
        for confidence, class_id in zip(detections.confidence, detections.class_id)
    ]

    # Annotate and display the frame
    annotated_frame = frame.copy()
    annotated_frame = box_annotator.annotate(scene=annotated_frame, detections=detections)
    annotated_frame = label_annotator.annotate(scene=annotated_frame, detections=detections, labels=labels)

    # # Display annotated frame
    # plt.figure(figsize=(12, 12))
    # plt.imshow(annotated_frame)
    # plt.title("Annotated Frame with Detections")
    # plt.axis('off')
    # plt.show()

    # Cell 4: Dynamic Line Zone Configuration
    video_info = sv.VideoInfo.from_video_path(SOURCE_VIDEO_PATH)

    # Define line position as a proportion of video height and width
    LINE_START = sv.Point(int(video_info.width * 0.02), int(video_info.height * 0.7))
    LINE_END = sv.Point(int(video_info.width * 0.98), int(video_info.height * 0.7))
    # LINE_START = sv.Point(0 + 50, 1500)
    # LINE_END = sv.Point(3840 - 50, 1500)

    TARGET_VIDEO_PATH = f"{HOME}/result.mp4"

    # print(f"Line Start: {LINE_START}, Line End: {LINE_END}")
    # print(f"Video Dimensions - Width: {video_info.width}, Height: {video_info.height}")

    # Cell 5: Set up Trackers, Counters, and Annotators
    in_count, out_count = 0, 0
    byte_tracker = sv.ByteTrack(
        track_activation_threshold=0.25,
        lost_track_buffer=30,
        minimum_matching_threshold=0.8,
        frame_rate=30,
        minimum_consecutive_frames=3
    )
    byte_tracker.reset()

    # line_zone = sv.LineZone(start=LINE_START, end=LINE_END)
    trace_annotator = sv.TraceAnnotator(thickness=4, trace_length=50)
    line_zone_annotator = sv.LineZoneAnnotator(thickness=4, text_thickness=4, text_scale=2)

    # print("Trackers, counters, and annotators initialized.")


    import supervision as sv
    import numpy as np
    from dataclasses import dataclass
    from typing import Dict, Tuple, List
    import cv2

    @dataclass
    class VehicleTrajectory:
        """Stores complete trajectory information for a vehicle"""
        id: int
        positions: List[Tuple[float, float]]  # Center positions (x, y)
        areas: List[float]
        first_seen: int
        last_seen: int
        counted: bool = False
        direction: str = None

    class SideViewTracker:
        """Specialized tracker for side-view camera setup"""
        def __init__(
            self,
            min_trajectory_length: int = 8,        # Reduced due to side view
            area_change_threshold: float = 0.3,    # Adjusted for side perspective
            smoothing_window: int = 3,             # Reduced for more responsive tracking
            position_change_weight: float = 0.7,   # Weight for position vs size change
            min_horizontal_movement: float = 50    # Minimum pixels of horizontal movement
        ):
            self.trajectories: Dict[int, VehicleTrajectory] = {}
            self.completed_trajectories: Dict[int, VehicleTrajectory] = {}
            self.min_trajectory_length = min_trajectory_length
            self.area_change_threshold = area_change_threshold
            self.smoothing_window = smoothing_window
            self.position_change_weight = position_change_weight
            self.min_horizontal_movement = min_horizontal_movement
            self.frame_count = 0
            self.in_count = 0
            self.out_count = 0
        
        def get_box_center_and_area(self, box: np.ndarray) -> Tuple[Tuple[float, float], float]:
            """Calculate box center position and area"""
            x1, y1, x2, y2 = box
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
            area = (x2 - x1) * (y2 - y1)
            return (center_x, center_y), area

        def analyze_trajectory(self, trajectory: VehicleTrajectory) -> str:
            """Analyze trajectory considering both position and size changes"""
            if len(trajectory.positions) < self.min_trajectory_length:
                return None

            # Analyze horizontal movement
            start_x = trajectory.positions[0][0]
            end_x = trajectory.positions[-1][0]
            horizontal_movement = end_x - start_x

            # Only count if there's significant horizontal movement
            if abs(horizontal_movement) < self.min_horizontal_movement:
                return None

            # Calculate size change
            size_change = (trajectory.areas[-1] - trajectory.areas[0]) / trajectory.areas[0]

            # Combine position and size information for decision
            if horizontal_movement > 0:  # Moving right in frame
                return 'in' if size_change > -self.area_change_threshold else 'out'
            else:  # Moving left in frame
                return 'out' if size_change > -self.area_change_threshold else 'in'

        def update(self, detections: sv.Detections) -> Tuple[List[int], List[int]]:
            """Update trajectories and count vehicles"""
            self.frame_count += 1
            current_in_ids = []
            current_out_ids = []
            current_ids = set(detections.tracker_id)

            # Update existing trajectories and add new ones
            for idx, (tracker_id, box) in enumerate(zip(detections.tracker_id, detections.xyxy)):
                center, area = self.get_box_center_and_area(box)
                
                if tracker_id not in self.trajectories:
                    self.trajectories[tracker_id] = VehicleTrajectory(
                        id=tracker_id,
                        positions=[center],
                        areas=[area],
                        first_seen=self.frame_count,
                        last_seen=self.frame_count
                    )
                else:
                    self.trajectories[tracker_id].positions.append(center)
                    self.trajectories[tracker_id].areas.append(area)
                    self.trajectories[tracker_id].last_seen = self.frame_count

            # Process disappeared vehicles
            disappeared_ids = set(self.trajectories.keys()) - current_ids
            for track_id in disappeared_ids:
                trajectory = self.trajectories[track_id]
                
                if not trajectory.counted:
                    direction = self.analyze_trajectory(trajectory)
                    if direction == 'in':
                        self.in_count += 1
                        current_in_ids.append(track_id)
                        trajectory.direction = 'in'
                        trajectory.counted = True
                    elif direction == 'out':
                        self.out_count += 1
                        current_out_ids.append(track_id)
                        trajectory.direction = 'out'
                        trajectory.counted = True
                        
                self.completed_trajectories[track_id] = trajectory
                del self.trajectories[track_id]

            return current_in_ids, current_out_ids

        def get_counts(self) -> Tuple[int, int]:
            """Return the current in and out counts"""
            return self.in_count, self.out_count

    def callback(frame: np.ndarray, index: int) -> np.ndarray:
        # Model prediction and conversion to supervision Detections
        results = model(frame, verbose=False)[0]
        detections = sv.Detections.from_ultralytics(results)
        
        # Filter for selected classes
        detections = detections[np.isin(detections.class_id, SELECTED_CLASS_IDS)]
        
        # Track detections
        detections = byte_tracker.update_with_detections(detections)
        
        # Update trajectory tracking
        current_in_ids, current_out_ids = trajectory_tracker.update(detections)
        
        # Create labels with movement indication
        labels = []
        for confidence, class_id, tracker_id in zip(
            detections.confidence, detections.class_id, detections.tracker_id):
            
            movement = ""
            if tracker_id in current_in_ids:
                movement = "→ IN"
            elif tracker_id in current_out_ids:
                movement = "← OUT"
            
            labels.append(
                f"#{tracker_id} {model.model.names[class_id]} {confidence:0.2f} {movement}"
            )
        
        # Annotate frame
        annotated_frame = frame.copy()
        annotated_frame = trace_annotator.annotate(scene=annotated_frame, detections=detections)
        annotated_frame = box_annotator.annotate(scene=annotated_frame, detections=detections)
        annotated_frame = label_annotator.annotate(
            scene=annotated_frame, detections=detections, labels=labels
        )
        
        # Add count overlay
        in_count, out_count = trajectory_tracker.get_counts()
        counts_text = f"IN: {in_count} OUT: {out_count}"
        cv2.putText(
            annotated_frame, counts_text,
            (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3
        )
        
        return annotated_frame

    # Initialize trackers
    byte_tracker = sv.ByteTrack(
        track_activation_threshold=0.25,
        lost_track_buffer=30,
        minimum_matching_threshold=0.8,
        frame_rate=30,
        minimum_consecutive_frames=3
    )
    trajectory_tracker = SideViewTracker()

    # Process video
    sv.process_video(
        source_path=SOURCE_VIDEO_PATH,
        target_path="result_final.mp4",
        callback=callback
    )

    # Print final counts
    final_in, final_out = trajectory_tracker.get_counts()
    # print(f"Final counts - IN: {final_in}, OUT: {final_out}")
    return final_in, final_out
x,y = yolo()
print(x,y)

