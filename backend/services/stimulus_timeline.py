"""
EyeInsight stimulus timeline.

This module mirrors the frontend stimulus phases used during recording.
Keeping the timeline centralized makes it possible to convert raw video frames
into phase-aware feature tables.

IMPORTANT: This is a research/MVP pipeline. It does not diagnose ASD.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
import math
from typing import Optional


@dataclass(frozen=True)
class StimulusPhase:
    name: str
    start_sec: float
    end_sec: float
    stimulus_type: str
    expected_target: str

    @property
    def duration_sec(self) -> float:
        return self.end_sec - self.start_sec


# Must match frontend ScreeningPage.tsx durations.
STIMULUS_TIMELINE: list[StimulusPhase] = [
    StimulusPhase("center_focus", 0.0, 5.0, "center_cross", "center"),
    StimulusPhase("horizontal_tracking", 5.0, 15.0, "moving_dot_horizontal", "moving_horizontal"),
    StimulusPhase("vertical_tracking", 15.0, 25.0, "moving_dot_vertical", "moving_vertical"),
    StimulusPhase("social_face", 25.0, 35.0, "smiling_face", "center"),
    StimulusPhase("attention_shift", 35.0, 45.0, "colorful_object", "left_right_shift"),
    StimulusPhase("final_center", 45.0, 50.0, "finish_center", "center"),
]


def get_phase_at(timestamp_sec: float) -> Optional[StimulusPhase]:
    for phase in STIMULUS_TIMELINE:
        if phase.start_sec <= timestamp_sec < phase.end_sec:
            return phase
    if abs(timestamp_sec - STIMULUS_TIMELINE[-1].end_sec) < 1e-6:
        return STIMULUS_TIMELINE[-1]
    return None


def timeline_as_dicts() -> list[dict]:
    return [asdict(phase) for phase in STIMULUS_TIMELINE]


def get_target_at(timestamp_sec: float) -> dict[str, float | str] | None:
    """Return the designed stimulus position in normalized screen coordinates.

    Coordinates mirror the browser animations closely enough for an experimental
    gaze-to-target proxy. They are not a calibrated eye-tracker coordinate system.
    """
    phase = get_phase_at(timestamp_sec)
    if phase is None:
        return None
    elapsed = timestamp_sec - phase.start_sec
    if phase.name == "horizontal_tracking":
        return {"x": _oscillating_position(elapsed, 0.13, 0.87), "y": 0.5, "zone": "moving_target"}
    if phase.name == "vertical_tracking":
        return {"x": 0.5, "y": _oscillating_position(elapsed, 0.13, 0.80), "zone": "moving_target"}
    if phase.name == "attention_shift":
        return {"x": 0.18 if elapsed % 2.0 < 1.0 else 0.82, "y": 0.5, "zone": "attention_shift_target"}
    if phase.name == "social_face":
        return {"x": 0.5, "y": 0.46, "zone": "social_face"}
    return {"x": 0.5, "y": 0.5, "zone": "center"}


def _oscillating_position(elapsed: float, start: float, end: float) -> float:
    half_cycle = 1.8
    cycle_position = elapsed % (half_cycle * 2)
    if cycle_position <= half_cycle:
        progress = cycle_position / half_cycle
        eased = (1 - math.cos(math.pi * progress)) / 2
        return start + (end - start) * eased
    progress = (cycle_position - half_cycle) / half_cycle
    eased = (1 - math.cos(math.pi * progress)) / 2
    return end - (end - start) * eased
