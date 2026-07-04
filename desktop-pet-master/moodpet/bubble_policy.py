from dataclasses import dataclass
from typing import Callable, Optional, Protocol

from moodpet.emotion import EmotionState


FREQUENCY_COOLDOWN_SECONDS = {
    "high": 60,
    "medium": 180,
    "low": 600,
}

DO_NOT_DISTURB_MIN_SECONDS = 300
MAX_BUBBLE_LENGTH = 36
DEFAULT_REPLY = "我在旁边陪你，先做一步就好。"
ALLOWED_TARGET_IDS = {"realtime", "todo", "games", "settings"}
LOW_MOOD_EMOTIONS = {"sad", "angry", "disgust", "fear"}
PLAYFUL_EMOTIONS = {"happy", "surprise"}


@dataclass(frozen=True)
class BubbleSettings:
    frequency: str = "medium"
    do_not_disturb: bool = False
    jump_target: str = ""


@dataclass(frozen=True)
class BubbleContext:
    emotion_state: EmotionState
    settings: BubbleSettings
    recent_reply: str = ""
    user_locale: str = "zh-CN"


@dataclass(frozen=True)
class BubbleReply:
    text: str
    target_id: str
    source: str = "local"


@dataclass(frozen=True)
class BubblePrompt:
    emotion: str
    label_zh: str
    confidence: float
    target_id: str
    max_length: int
    style_rule: str
    safety_rule: str
    recent_reply: str = ""


class BubbleReplyProvider(Protocol):
    def generate(self, context: BubbleContext) -> BubbleReply:
        ...


class BubbleModelClient(Protocol):
    def complete(self, prompt: BubblePrompt) -> str:
        ...


def can_emit_bubble(settings: BubbleSettings, now_seconds: int, last_emit_seconds: Optional[int]) -> bool:
    if last_emit_seconds is None:
        return True

    elapsed = max(0, int(now_seconds) - int(last_emit_seconds))
    cooldown = FREQUENCY_COOLDOWN_SECONDS.get(settings.frequency, FREQUENCY_COOLDOWN_SECONDS["medium"])
    if settings.do_not_disturb:
        cooldown = max(cooldown, DO_NOT_DISTURB_MIN_SECONDS)
    return elapsed >= cooldown


def target_for_emotion(emotion: str) -> str:
    if emotion in LOW_MOOD_EMOTIONS:
        return "todo"
    if emotion in PLAYFUL_EMOTIONS:
        return "games"
    return "realtime"


def sanitize_user_bubble_reply(text: str) -> str:
    clean_text = " ".join(str(text).replace("\n", " ").replace("\r", " ").strip().split())
    if not clean_text:
        return DEFAULT_REPLY
    return clean_text[:MAX_BUBBLE_LENGTH]


def normalize_target_id(target_id: str) -> str:
    return target_id if target_id in ALLOWED_TARGET_IDS else "realtime"


def build_model_prompt(context: BubbleContext) -> BubblePrompt:
    emotion = context.emotion_state.emotion
    target_id = normalize_target_id(context.settings.jump_target) if context.settings.jump_target else target_for_emotion(emotion)
    return BubblePrompt(
        emotion=emotion,
        label_zh=context.emotion_state.label_zh,
        confidence=context.emotion_state.confidence,
        target_id=target_id,
        max_length=MAX_BUBBLE_LENGTH,
        style_rule="中文、温柔、短句、像桌宠主动提醒，不说教。",
        safety_rule="不要输出诊断、医疗建议、负面刺激、换行或超过长度限制。",
        recent_reply=context.recent_reply,
    )


class LocalRuleBubbleProvider:
    def generate(self, context: BubbleContext) -> BubbleReply:
        emotion = context.emotion_state.emotion
        target_id = normalize_target_id(context.settings.jump_target) if context.settings.jump_target else target_for_emotion(emotion)
        replies = {
            "happy": "状态不错，要不要玩一局放松一下？",
            "surprise": "有新发现啦，休息小游戏也不错。",
            "sad": "你看起来有点累，先完成一个小任务。",
            "angry": "先做一个小任务，把节奏稳回来。",
            "disgust": "换个小任务缓一缓，不急。",
            "fear": "别急，先做一个小任务就好。",
            "away": "回来后我继续陪你观察状态。",
            "disabled": "摄像头关闭中，也可以手动打开实时检测。",
            "error": "识别有点异常，功能导航仍可使用。",
            "neutral": "状态很稳，实时检测页可以看看趋势。",
        }
        return BubbleReply(sanitize_user_bubble_reply(replies.get(emotion, DEFAULT_REPLY)), target_id, source="local")


class ColdStartBubbleProvider:
    def generate(self, context: BubbleContext) -> BubbleReply:
        emotion = context.emotion_state.emotion
        target_id = normalize_target_id(context.settings.jump_target) if context.settings.jump_target else target_for_emotion(emotion)
        if emotion in LOW_MOOD_EMOTIONS:
            text = "先做一个很小的任务，我陪你稳住节奏。"
        elif emotion in PLAYFUL_EMOTIONS:
            text = "状态不错，点我去小游戏放松一下。"
        else:
            text = DEFAULT_REPLY
        return BubbleReply(sanitize_user_bubble_reply(text), target_id, source="cold_start")


class ModelBubbleProvider:
    def __init__(self, client: BubbleModelClient, fallback: Optional[BubbleReplyProvider] = None) -> None:
        self.client = client
        self.fallback = fallback or ColdStartBubbleProvider()

    def generate(self, context: BubbleContext) -> BubbleReply:
        prompt = build_model_prompt(context)
        try:
            text = self.client.complete(prompt)
        except Exception:
            return self.fallback.generate(context)
        return BubbleReply(sanitize_user_bubble_reply(text), prompt.target_id, source="model")


class CallableModelClient:
    def __init__(self, complete_func: Callable[[BubblePrompt], str]) -> None:
        self.complete_func = complete_func

    def complete(self, prompt: BubblePrompt) -> str:
        return self.complete_func(prompt)


def build_bubble_reply(context: BubbleContext, provider: Optional[BubbleReplyProvider] = None) -> BubbleReply:
    active_provider = provider or LocalRuleBubbleProvider()
    reply = active_provider.generate(context)
    return BubbleReply(sanitize_user_bubble_reply(reply.text), normalize_target_id(reply.target_id), reply.source)
