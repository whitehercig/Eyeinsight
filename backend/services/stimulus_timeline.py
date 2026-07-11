"""
EyeInsight stimulus timeline.

This module mirrors the frontend stimulus phases used during recording.
Keeping the timeline centralized makes it possible to convert raw video frames
into phase-aware feature tables.

IMPORTANT: This is a research/MVP pipeline. It does not diagnose ASD.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
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
