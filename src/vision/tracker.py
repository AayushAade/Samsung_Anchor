import numpy as np
from typing import List, Dict, Any


class FaceTracker:
    """
    FaceTracker class responsible for maintaining stable temporary track IDs
    for detected faces across video frames using IoU and centroid distance.
    """

    def __init__(
        self,
        iou_threshold: float = 0.3,
        distance_threshold: float = 100.0,
        max_lost_frames: int = 30,
    ):
        """
        Initializes the FaceTracker.

        Args:
            iou_threshold: Minimum Intersection-over-Union (IoU) to consider
                           a detection as a match for an existing track.
            distance_threshold: Maximum centroid distance (in pixels) to consider
                               a match if IoU is low.
            max_lost_frames: Number of consecutive frames a track can be missed
                             before it is removed.
        """
        self.iou_threshold = iou_threshold
        self.distance_threshold = distance_threshold
        self.max_lost_frames = max_lost_frames

        # Store active tracks: temp_id -> track_info dict
        # track_info has keys: 'bbox', 'center', 'lost_frames'
        self.active_tracks: Dict[str, Dict[str, Any]] = {}
        self.next_track_number = 1

    def _compute_iou(self, boxA: List[int], boxB: List[int]) -> float:
        """
        Computes Intersection-over-Union (IoU) of two bounding boxes.

        Args:
            boxA: [x1, y1, x2, y2]
            boxB: [x1, y1, x2, y2]

        Returns:
            IoU value between 0.0 and 1.0.
        """
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])

        inter_area = max(0, xB - xA) * max(0, yB - yA)
        boxA_area = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
        boxB_area = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
        union_area = boxA_area + boxB_area - inter_area

        if union_area <= 0:
            return 0.0
        return inter_area / float(union_area)

    def _compute_centroid(self, box: List[int]) -> np.ndarray:
        """
        Computes the center coordinate (cx, cy) of a bounding box.

        Args:
            box: [x1, y1, x2, y2]

        Returns:
            Numpy array [cx, cy] of centroid.
        """
        cx = (box[0] + box[2]) // 2
        cy = (box[1] + box[3]) // 2
        return np.array([cx, cy])

    def update(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Updates the tracker with the current frame's detections and assigns stable IDs.

        Args:
            detections: List of detection dicts from FaceDetector, each containing:
                        - 'bbox': [x1, y1, x2, y2]
                        - 'landmarks': list of landmarks
                        - 'confidence': confidence score

        Returns:
            The list of detections updated with a 'track_id' field.
        """
        updated_tracks = {}
        output_detections = []

        # Copy detections to avoid modifying input arguments directly
        unassociated_detections = [dict(det) for det in detections]

        # Match detections to existing tracks
        # Loop through existing tracks copy to decide their fate
        for temp_id, track in list(self.active_tracks.items()):
            track_box = track["bbox"]
            track_center = track["center"]

            best_det_idx = -1
            best_score = -1.0

            for idx, det in enumerate(unassociated_detections):
                det_box = det["bbox"]
                det_center = self._compute_centroid(det_box)

                iou = self._compute_iou(det_box, track_box)
                dist = np.linalg.norm(det_center - track_center)

                is_match = False
                score = 0.0

                if iou > self.iou_threshold:
                    is_match = True
                    score = iou
                elif dist < self.distance_threshold:
                    is_match = True
                    # Higher similarity score for smaller distance
                    score = 1.0 / (dist + 1.0)

                if is_match and score > best_score:
                    best_score = score
                    best_det_idx = idx

            if best_det_idx != -1:
                # Associated detection found: update the track
                matched_det = unassociated_detections.pop(best_det_idx)
                
                det_box = matched_det["bbox"]
                det_center = self._compute_centroid(det_box)

                updated_tracks[temp_id] = {
                    "bbox": det_box,
                    "center": det_center,
                    "lost_frames": 0,
                }
                
                matched_det["track_id"] = temp_id
                output_detections.append(matched_det)
            else:
                # No matching detection: keep track but increment lost frames count
                track["lost_frames"] += 1
                if track["lost_frames"] <= self.max_lost_frames:
                    updated_tracks[temp_id] = track

        # For remaining unassociated detections, create new tracks
        for det in unassociated_detections:
            new_id = f"Temp_{self.next_track_number}"
            self.next_track_number += 1
            
            det_box = det["bbox"]
            det_center = self._compute_centroid(det_box)

            updated_tracks[new_id] = {
                "bbox": det_box,
                "center": det_center,
                "lost_frames": 0,
            }
            
            det["track_id"] = new_id
            output_detections.append(det)

        self.active_tracks = updated_tracks
        return output_detections
