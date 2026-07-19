"""MediaPipe Face Mesh primitives used by EyeInsight's video pipeline."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import cv2
import numpy as np

try:
    import mediapipe as mp
except ImportError as exc:  # pragma: no cover - dependency is declared in requirements
    raise RuntimeError("MediaPipe is required. Install backend/requirements.txt before starting EyeInsight.") from exc


LEFT_EYE = (33, 160, 158, 133, 153, 144)
RIGHT_EYE = (362, 385, 387, 263, 373, 380)
LEFT_IRIS = (468, 469, 470, 471, 472)
RIGHT_IRIS = (473, 474, 475, 476, 477)
POSE_LANDMARKS = (1, 152, 33, 263, 61, 291)
POSE_MODEL_POINTS = np.array(
    [(0.0, 0.0, 0.0), (0.0, -63.6, -12.5), (-43.3, 32.7, -26.0), (43.3, 32.7, -26.0), (-28.9, -28.9, -24.1), (28.9, -28.9, -24.1)],
    dtype=np.float64,
)


def _distance(first: np.ndarray, second: np.ndarray) -> float:
    return float(np.linalg.norm(first - second))


def _ear(points: np.ndarray) -> float:
    horizontal = _distance(points[0], points[3])
    if horizontal < 1e-8:
        return 0.0
    return (_distance(points[1], points[5]) + _distance(points[2], points[4])) / (2.0 * horizontal)


def _mean_point(points: np.ndarray, indexes: tuple[int, ...]) -> np.ndarray | None:
    available = [points[index] for index in indexes if index < len(points)]
    return np.mean(available, axis=0) if available else None


def _normalize_pitch(angle: float) -> float:
    """Map the equivalent 180° solvePnP representation to a frontal pitch."""
    normalized = (angle + 180.0) % 360.0 - 180.0
    if normalized > 90.0:
        return 180.0 - normalized
    if normalized < -90.0:
        return -180.0 - normalized
    return normalized


@dataclass
class TrackingState:
    previous_pose: np.ndarray | None = None
    previous_center: np.ndarray | None = None
    previous_timestamp: float | None = None
    smoothed_gaze: np.ndarray | None = None
    blink_started_at: float | None = None
    blink_count: int = 0


class FaceMeshProcessor:
    """Stateful Face Mesh processor with blink, gaze, and pose continuity."""

    def __init__(self) -> None:
        self._mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.state = TrackingState()

    def close(self) -> None:
        self._mesh.close()

    def __enter__(self) -> "FaceMeshProcessor":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def process(self, frame: np.ndarray, timestamp: float) -> dict[str, Any]:
        height, width = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self._mesh.process(rgb)
        if not result.multi_face_landmarks:
            return self._lost_frame(timestamp)

        landmark_list = result.multi_face_landmarks[0].landmark
        points = np.array([(landmark.x, landmark.y, landmark.z) for landmark in landmark_list], dtype=np.float64)
        min_xy, max_xy = points[:, :2].min(axis=0), points[:, :2].max(axis=0)
        center = (min_xy + max_xy) / 2.0
        face_width, face_height = max_xy - min_xy
        face_area = float(face_width * face_height)
        center_offset = float(np.linalg.norm(center - np.array([0.5, 0.5])))

        left_eye = points[list(LEFT_EYE), :2]
        right_eye = points[list(RIGHT_EYE), :2]
        ear_left, ear_right = _ear(left_eye), _ear(right_eye)
        ear_mean = (ear_left + ear_right) / 2.0
        blink, blink_duration = self._blink(ear_mean, timestamp)
        gaze_x, gaze_y = self._gaze(points)
        yaw, pitch, roll = self._pose(points, width, height)
        head_motion, head_stability, rotation_velocity = self._motion(np.array([yaw, pitch, roll]), center, timestamp)
        eyes_detected = len(points) > max(RIGHT_EYE) and ear_mean > 0.03
        tracking_confidence = float(np.clip(
            0.40 + 0.25 * float(eyes_detected) + 0.20 * min(face_area / 0.08, 1.0) + 0.15 * max(0.0, 1.0 - center_offset / 0.5), 0.0, 1.0
        ))
        direction = self._direction(gaze_x, gaze_y, yaw, pitch, tracking_confidence)
        return {
            "face_detected": 1,
            "left_eye_detected": int(eyes_detected),
            "right_eye_detected": int(eyes_detected),
            "face_center_x": round(float(center[0]), 6),
            "face_center_y": round(float(center[1]), 6),
            "face_width": round(float(face_width), 6),
            "face_height": round(float(face_height), 6),
            "face_area_ratio": round(face_area, 6),
            "distance_proxy": round(float(np.clip(face_width / 0.35, 0.0, 3.0)), 6),
            "yaw": round(yaw, 4),
            "pitch": round(pitch, 4),
            "roll": round(roll, 4),
            "head_rotation_velocity": round(rotation_velocity, 5),
            "head_motion": round(head_motion, 5),
            "head_stability": round(head_stability, 5),
            "head_displacement": round(head_motion, 5),
            "ear_left": round(ear_left, 5),
            "ear_right": round(ear_right, 5),
            "eye_openness": round(ear_mean, 5),
            "blink": blink,
            "blink_duration": round(blink_duration, 4),
            "blink_probability": round(float(np.clip((0.22 - ear_mean) / 0.07, 0.0, 1.0)), 5),
            "gaze_x": round(gaze_x, 5),
            "gaze_y": round(gaze_y, 5),
            "looking_direction": direction,
            "tracking_confidence": round(tracking_confidence, 5),
            "center_offset": round(center_offset, 5),
        }

    def _lost_frame(self, timestamp: float) -> dict[str, Any]:
        if self.state.blink_started_at is not None:
            self.state.blink_started_at = None
        self.state.previous_timestamp = timestamp
        return {"face_detected": 0, "left_eye_detected": 0, "right_eye_detected": 0, "face_center_x": np.nan, "face_center_y": np.nan, "face_width": 0.0, "face_height": 0.0, "face_area_ratio": 0.0, "distance_proxy": 0.0, "yaw": np.nan, "pitch": np.nan, "roll": np.nan, "head_rotation_velocity": 0.0, "head_motion": 0.0, "head_stability": 0.0, "head_displacement": 0.0, "ear_left": np.nan, "ear_right": np.nan, "eye_openness": np.nan, "blink": 0, "blink_duration": 0.0, "blink_probability": 0.0, "gaze_x": np.nan, "gaze_y": np.nan, "looking_direction": "tracking_lost", "tracking_confidence": 0.0, "center_offset": np.nan}

    def _blink(self, ear: float, timestamp: float) -> tuple[int, float]:
        closed = ear < 0.19
        if closed and self.state.blink_started_at is None:
            self.state.blink_started_at = timestamp
            return 0, 0.0
        if not closed and self.state.blink_started_at is not None:
            duration = max(0.0, timestamp - self.state.blink_started_at)
            self.state.blink_started_at = None
            if 0.04 <= duration <= 0.8:
                self.state.blink_count += 1
                return 1, duration
        return 0, 0.0

    def _gaze(self, points: np.ndarray) -> tuple[float, float]:
        left_iris, right_iris = _mean_point(points, LEFT_IRIS), _mean_point(points, RIGHT_IRIS)
        if left_iris is None or right_iris is None:
            return (0.0, 0.0) if self.state.smoothed_gaze is None else tuple(self.state.smoothed_gaze)
        def eye_ratio(iris: np.ndarray, outer: int, inner: int, top: int, bottom: int) -> tuple[float, float]:
            horizontal = max(1e-6, abs(points[inner, 0] - points[outer, 0]))
            vertical = max(1e-6, abs(points[bottom, 1] - points[top, 1]))
            return ((iris[0] - (points[outer, 0] + points[inner, 0]) / 2) / (horizontal / 2), (iris[1] - (points[top, 1] + points[bottom, 1]) / 2) / (vertical / 2))
        left = eye_ratio(left_iris, 33, 133, 159, 145)
        right = eye_ratio(right_iris, 263, 362, 386, 374)
        raw = np.clip(np.array([(left[0] + right[0]) / 2, (left[1] + right[1]) / 2]), -1.0, 1.0)
        self.state.smoothed_gaze = raw if self.state.smoothed_gaze is None else 0.30 * raw + 0.70 * self.state.smoothed_gaze
        return tuple(float(value) for value in self.state.smoothed_gaze)

    def _pose(self, points: np.ndarray, width: int, height: int) -> tuple[float, float, float]:
        image_points = np.array([(points[index, 0] * width, points[index, 1] * height) for index in POSE_LANDMARKS], dtype=np.float64)
        focal = float(width)
        camera = np.array([[focal, 0, width / 2], [0, focal, height / 2], [0, 0, 1]], dtype=np.float64)
        success, rotation, _ = cv2.solvePnP(POSE_MODEL_POINTS, image_points, camera, np.zeros((4, 1)), flags=cv2.SOLVEPNP_ITERATIVE)
        if not success:
            return 0.0, 0.0, 0.0
        matrix, _ = cv2.Rodrigues(rotation)
        angles, *_ = cv2.RQDecomp3x3(matrix)
        raw_pitch, yaw, roll = (float(angle) for angle in angles)
        pitch = _normalize_pitch(raw_pitch)
        return yaw, pitch, roll

    def _motion(self, pose: np.ndarray, center: np.ndarray, timestamp: float) -> tuple[float, float, float]:
        delta_time = max(1e-3, timestamp - self.state.previous_timestamp) if self.state.previous_timestamp is not None else 1.0
        pose_delta = float(np.linalg.norm(pose - self.state.previous_pose)) if self.state.previous_pose is not None else 0.0
        displacement = float(np.linalg.norm(center - self.state.previous_center)) if self.state.previous_center is not None else 0.0
        velocity = pose_delta / delta_time
        motion = displacement + min(1.0, velocity / 100.0)
        self.state.previous_pose, self.state.previous_center, self.state.previous_timestamp = pose, center, timestamp
        return motion, float(np.clip(1.0 - motion * 2.0, 0.0, 1.0)), velocity

    @staticmethod
    def _direction(gaze_x: float, gaze_y: float, yaw: float, pitch: float, confidence: float) -> str:
        if confidence < 0.45:
            return "tracking_lost"
        if abs(yaw) > 32 or abs(pitch) > 28 or abs(gaze_x) > 0.70 or abs(gaze_y) > 0.70:
            return "looking_away"
        if gaze_x < -0.22:
            return "looking_left"
        if gaze_x > 0.22:
            return "looking_right"
        if gaze_y < -0.22:
            return "looking_up"
        if gaze_y > 0.22:
            return "looking_down"
        return "looking_center"
