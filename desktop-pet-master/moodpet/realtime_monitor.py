from dataclasses import dataclass
from typing import List, Sequence, Tuple

from moodpet.emotion import EmotionState, build_emotion_state


EMOTION_EN_LABELS = {
    "angry": "angry",
    "disgust": "disgust",
    "fear": "nervous",
    "happy": "happy",
    "sad": "sad",
    "surprise": "surprise",
    "neutral": "neutral",
    "unknown": "observing",
    "away": "away",
    "disabled": "offline",
    "error": "error",
}

EMOTION_SCORE_BASE = {
    "happy": 86,
    "neutral": 62,
    "surprise": 78,
    "sad": 34,
    "angry": 28,
    "disgust": 30,
    "fear": 42,
    "away": 18,
    "unknown": 52,
    "disabled": 0,
    "error": 8,
}

TREND_TIMES = ["00:00", "03:00", "06:00", "09:00", "12:00", "15:00", "18:00", "21:00", "24:00"]
TREND_BASE = [48, 32, 86, 52, 68, 34, 82, 51, 70]


@dataclass(frozen=True)
class MonitorRow:
    title: str
    value: str
    icon: str


def emotion_english_label(emotion: str) -> str:
    return EMOTION_EN_LABELS.get((emotion or "unknown").lower(), "observing")


def confidence_percent(state: EmotionState) -> int:
    if state.confidence > 0:
        return int(round(max(0.0, min(state.confidence, 1.0)) * 100))
    return EMOTION_SCORE_BASE.get(state.emotion, EMOTION_SCORE_BASE["unknown"])


def monitor_status_text(enabled: bool, emotion: str) -> str:
    if not enabled:
        return "待开启"
    if emotion == "error":
        return "异常"
    if emotion == "away":
        return "未检测到人脸"
    return "识别中"


def build_monitor_rows(state: EmotionState, enabled: bool) -> List[MonitorRow]:
    return [
        MonitorRow("当前情绪", state.label_zh, "☻"),
        MonitorRow("英文标签", emotion_english_label(state.emotion), "▣"),
        MonitorRow("置信度", f"{confidence_percent(state)}%", "▥"),
        MonitorRow("状态", monitor_status_text(enabled, state.emotion), "◎"),
    ]


def build_trend_points(state: EmotionState, enabled: bool) -> List[Tuple[str, int]]:
    if not enabled:
        return list(zip(TREND_TIMES, TREND_BASE))

    current = confidence_percent(state)
    points = list(TREND_BASE)
    points[-2] = current
    points[-1] = min(100, max(0, int((current + points[-3]) / 2)))
    return list(zip(TREND_TIMES, points))


def preview_badge_text(enabled: bool, state: EmotionState) -> str:
    if not enabled:
        return "摄像头待开启"
    if state.emotion == "error":
        return "摄像头异常"
    if state.emotion == "away":
        return "等待人脸进入"
    return "摄像头预览中"


def monitor_summary(state: EmotionState, enabled: bool) -> str:
    rows = build_monitor_rows(state, enabled)
    return "，".join(f"{row.title}：{row.value}" for row in rows)


def default_monitor_state() -> EmotionState:
    return build_emotion_state("happy", 0.86, True, "我会默默陪伴你，记录每一种情绪。")


def clamp_trend_values(points: Sequence[Tuple[str, int]]) -> List[Tuple[str, int]]:
    return [(time, min(100, max(0, int(value)))) for time, value in points]
