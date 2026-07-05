from dataclasses import dataclass
from typing import Dict, Optional


EMOTION_LABELS = [
    "neutral",
    "happy",
    "surprise",
    "sad",
    "angry",
    "disgust",
    "fear",
]

FERPLUS_LABELS = [
    "neutral",
    "happy",
    "surprise",
    "sad",
    "angry",
    "disgust",
    "fear",
    "contempt",
]

OPENVINO_EMOTION_LABELS = [
    "neutral",
    "happy",
    "sad",
    "surprise",
    "anger",
]

OPENVINO_TO_MOODPET = {
    "neutral": "neutral",
    "happy": "happy",
    "surprise": "surprise",
    "sad": "sad",
    "anger": "angry",
}

FERPLUS_TO_MOODPET = {
    "neutral": "neutral",
    "happy": "happy",
    "surprise": "happy",
    "sad": "sad",
    "angry": "sad",
    "disgust": "sad",
    "fear": "sad",
    "contempt": "sad",
}

EMOTION_ZH = {
    "angry": "生气",
    "disgust": "厌恶",
    "fear": "紧张",
    "happy": "开心",
    "sad": "低落",
    "surprise": "惊讶",
    "neutral": "平静",
    "unknown": "未知",
    "away": "离开",
    "disabled": "未启用",
    "error": "异常",
}

PET_TALKS = {
    "happy": "你看起来心情不错，继续保持呀。",
    "neutral": "现在状态很平稳，我在旁边陪你。",
    "surprise": "好像有什么新发现？我也精神起来了。",
    "sad": "看起来有点低落，要不要先完成一个很小的任务？",
    "angry": "先慢一点，深呼吸一下再继续。",
    "disgust": "这个状态不太舒服，要不要换个任务缓一缓？",
    "fear": "别急，我陪你一步一步来。",
    "away": "我暂时没看到你，回来后继续陪你。",
    "disabled": "情绪识别未启用，可以在右键菜单里开启。",
    "error": "情绪识别遇到一点问题，桌宠功能仍可继续使用。",
    "unknown": "我还在观察你的状态。",
}


@dataclass(frozen=True)
class EmotionState:
    emotion: str
    label_zh: str
    confidence: float
    face_detected: bool
    message: str

    def display_text(self) -> str:
        percent = int(round(self.confidence * 100))
        if self.emotion in {"disabled", "error", "away", "unknown"}:
            return f"状态：{self.label_zh}\n{self.message}"
        return f"情绪：{self.label_zh}（{percent}%）\n{self.message}"


def emotion_to_zh(emotion: Optional[str]) -> str:
    if not emotion:
        return EMOTION_ZH["unknown"]
    return EMOTION_ZH.get(emotion.lower(), EMOTION_ZH["unknown"])


def build_emotion_state(
    emotion: Optional[str],
    confidence: float = 0.0,
    face_detected: bool = True,
    message: Optional[str] = None,
) -> EmotionState:
    normalized = (emotion or "unknown").lower()
    if not face_detected:
        normalized = "away"
    if normalized not in EMOTION_ZH:
        normalized = "unknown"

    safe_confidence = max(0.0, min(float(confidence), 1.0))
    return EmotionState(
        emotion=normalized,
        label_zh=emotion_to_zh(normalized),
        confidence=safe_confidence,
        face_detected=face_detected,
        message=message or PET_TALKS.get(normalized, PET_TALKS["unknown"]),
    )


def best_emotion(scores: Dict[str, float]) -> EmotionState:
    if not scores:
        return build_emotion_state("unknown", 0.0, False)

    normalized_scores = {key.lower(): float(value) for key, value in scores.items()}
    emotion, score = max(normalized_scores.items(), key=lambda item: item[1])
    if score > 1:
        score = score / 100
    return build_emotion_state(emotion, score, True)


def best_ferplus_emotion(scores: Dict[str, float]) -> EmotionState:
    return best_openvino_emotion(scores)


def best_openvino_emotion(scores: Dict[str, float]) -> EmotionState:
    if not scores:
        return build_emotion_state("unknown", 0.0, False)

    raw_emotion, score = max(
        ((key.lower(), float(value)) for key, value in scores.items()),
        key=lambda item: item[1],
    )
    moodpet_emotion = OPENVINO_TO_MOODPET.get(raw_emotion, "unknown")
    return build_emotion_state(moodpet_emotion, score, True)
