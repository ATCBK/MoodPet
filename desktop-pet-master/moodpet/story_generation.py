import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Mapping, Optional, Sequence

from moodpet.deepseek_bubble import load_env_file, post_json
from moodpet.emotion import EmotionState
from moodpet.mini_game_state import (
    MiniGameState,
    StoryChoice,
    StoryClue,
    StoryNode,
    StoryReward,
    build_default_game,
)


DEFAULT_DEEPSEEK_MODEL = "deepseek-v4-flash"
DEFAULT_TIMEOUT_SECONDS = 12.0
DEEPSEEK_CHAT_COMPLETIONS_URL = "https://api.deepseek.com/chat/completions"


@dataclass(frozen=True)
class StoryGenerationConfig:
    api_key: str
    model: str = DEFAULT_DEEPSEEK_MODEL
    timeout: float = DEFAULT_TIMEOUT_SECONDS


class DeepSeekStoryClient:
    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_DEEPSEEK_MODEL,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        post_json_func=post_json,
    ) -> None:
        self.api_key = api_key
        self.model = model or DEFAULT_DEEPSEEK_MODEL
        self.timeout = timeout
        self.post_json = post_json_func

    def complete(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是 MoodPet 的剧情生成器。你只输出严格 JSON，不要输出解释、代码块或多余文本。",
                },
                {"role": "user", "content": prompt},
            ],
            "thinking": {"type": "disabled"},
            "temperature": 0.8,
            "presence_penalty": 0.2,
            "frequency_penalty": 0.2,
            "max_tokens": 1600,
            "stream": False,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        response = self.post_json(DEEPSEEK_CHAT_COMPLETIONS_URL, payload, headers, self.timeout)
        text = self._extract_text(response)
        if not text:
            raise RuntimeError("DeepSeek returned empty content")
        return text

    @staticmethod
    def _extract_text(response: Mapping) -> str:
        try:
            content = response["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("DeepSeek response missing message content") from exc
        return str(content).strip()


def load_story_generation_config(values: Optional[Mapping[str, str]] = None, env_path: Optional[Path] = None) -> StoryGenerationConfig:
    file_values = load_env_file(env_path) if env_path is not None else {}
    merged = {**file_values, **(values or {}), **os.environ}
    timeout = float(merged.get("DEEPSEEK_TIMEOUT", DEFAULT_TIMEOUT_SECONDS))
    return StoryGenerationConfig(
        api_key=merged.get("DEEPSEEK_API_KEY", "").strip(),
        model=merged.get("DEEPSEEK_MODEL", DEFAULT_DEEPSEEK_MODEL).strip() or DEFAULT_DEEPSEEK_MODEL,
        timeout=timeout,
    )


def build_story_generation_prompt(emotion_state: EmotionState) -> str:
    emotion = emotion_state.emotion
    confidence_percent = int(round(emotion_state.confidence * 100))
    return (
        "请生成一套适合 MoodPet 小游戏的互动剧情，要求能结合当前用户情绪，帮助缓解负面情绪或放大轻松感。"
        "风格保持治愈、轻巧、细腻、可视化，故事主题固定为邮局/信件/时间/小伙伴陪伴的情绪冒险。"
        "如果当前情绪是 sad/angry/fear/disgust，要偏向安抚、降压、慢节奏、小成功感；"
        "如果当前情绪是 happy/surprise/neutral，要偏向轻快、探索、奖励和微小惊喜。"
        "请严格输出 JSON，不要输出 markdown，不要输出解释。JSON 结构如下："
        "{"
        '"story_title":"",'
        '"subtitle":"",'
        '"emotion_summary":"",'
        '"theme_subject":"",'
        '"theme_mood":"",'
        '"theme_style":"",'
        '"nodes":[{"id":"","title":"","prompt":"","scene_text":"","pet_reply":"","step_label":""}],'
        '"choices":[{"id":"","icon":"","title":"","next_node":2,"clue_id":""}],'
        '"clues":[{"id":"","icon":"","title":"","collected":false}],'
        '"rewards":[{"label":"","value":12,"icon":""}]'
        "}"
        " 约束："
        " nodes 必须正好 6 条，顺序固定为开场、事件、选择后、线索展开、行动、结尾；"
        " node_index=1 的那一页必须是玩家真正做选择的事件页；"
        " choices 必须正好 3 条，next_node 统一写 2；"
        " clues 必须正好 6 条，前三条 collected=true，后三条 collected=false；"
        " rewards 必须正好 3 条；"
        f" 当前情绪：{emotion}（{emotion_state.label_zh}），置信度 {confidence_percent}%；"
        f" 情绪提示语：{emotion_state.message}；"
        " story_title 不要超过 18 个汉字，subtitle 不要超过 28 个汉字，emotion_summary 不要超过 32 个汉字；"
        " 所有文案都要是中文，避免诊断性、指责性、恐吓性措辞。"
    )


class StoryGenerationService:
    def __init__(self, client: Optional[DeepSeekStoryClient], cache_dir: Path) -> None:
        self.client = client
        self.cache_dir = cache_dir

    def generate(self, emotion_state: EmotionState) -> MiniGameState:
        cached = self.load_cached_story(emotion_state)
        if cached is not None:
            return cached

        if self.client is not None:
            try:
                prompt = build_story_generation_prompt(emotion_state)
                text = self.client.complete(prompt)
                state = self._state_from_text(text, emotion_state)
                self.cache_story(emotion_state, state)
                return state
            except Exception:
                pass

        state = self.build_local_story(emotion_state)
        self.cache_story(emotion_state, state)
        return state

    def build_local_story(self, emotion_state: EmotionState) -> MiniGameState:
        profile = _emotion_profile(emotion_state)
        nodes = [
            StoryNode(
                "opening",
                f"{profile['story_title']}的第一盏灯",
                f"{emotion_state.label_zh} 的气息像窗边的雾，MoodPet 把一盏小灯放到桌边，让你先不用急着回答任何问题。",
                f"邮局里的灯光慢慢亮起来，空气里有纸张和木头的味道，像是在提醒你先停一停。",
                "先别赶路，我们把心情放稳，再往前看。",
                "开场",
            ),
            StoryNode(
                "event",
                "要先碰哪一个线索",
                f"MoodPet 发现桌上摆着三样东西：一封信、一只旧钟，还有一段像风一样轻的提示，正等你选一个最想靠近的。",
                f"窗外的雾还没有散完，但桌上的小物件都在安静发亮，像是在等你做一个不会出错的小决定。",
                "先选一个最轻松的方向就好，故事会跟着你慢慢展开。",
                "事件",
            ),
            StoryNode(
                "choice_result",
                "被点亮的回应",
                f"你选中的方向让邮局里的某个角落轻轻亮了起来，像是在说：这一步走得很好。",
                f"MoodPet 顺着你选的方向点了点头，原本安静的场景开始出现细小的回声和温暖的光。",
                "很好，我们已经找到第一点安心感了。",
                "选择",
            ),
            StoryNode(
                "clue_trace",
                "线索开始连起来",
                f"信件、钟声和那一缕提示慢慢连在一起，故事不再只是等待，而是在一点点变得清楚。",
                f"桌面上的纸张被轻轻摊开，原本模糊的地方逐渐有了形状，像是在替你把心里的结打开。",
                "不用着急，线索已经开始自己说话了。",
                "线索",
            ),
            StoryNode(
                "action",
                "把线索送到该去的地方",
                f"现在只差最后一步，你把刚刚收集到的线索拼好，准备把它送去最合适的位置，让事情往前走。",
                f"邮局深处的灯泡亮得更柔和了，MoodPet 跟在你旁边，像是在确认这次不会再迷路。",
                "我们已经走到最接近答案的地方了。",
                "行动",
            ),
            StoryNode(
                "ending",
                "雾散之后的小小落点",
                f"当最后一封信被放回正确的位置，空气里那点沉着的压力也跟着散开，留下更轻一点的呼吸。",
                f"夜色与暖灯一起落下来，邮局重新安静下来，但这一次安静里有了被照顾好的感觉。",
                "做得很好，情绪已经被轻轻托住了。",
                "结尾",
            ),
        ]
        choices = [
            StoryChoice("choice_letter", "✉", "先看那封信", 2, "clue_letter"),
            StoryChoice("choice_clock", "⏰", "跟着钟声慢慢走", 2, "clue_clock"),
            StoryChoice("choice_pet", "🐾", "让 MoodPet 带路", 2, "clue_pet"),
        ]
        clues = [
            StoryClue("stamp", "✦", "蓝色邮戳", True),
            StoryClue("clock", "◔", "慢半拍的钟声", True),
            StoryClue("address", "⌂", "未写完的地址", True),
            StoryClue("clue_letter", "✉", "信封边缘的暖痕", False),
            StoryClue("clue_clock", "⏰", "钟面的轻微停顿", False),
            StoryClue("clue_pet", "🐾", "MoodPet 的带路提示", False),
        ]
        rewards = [
            StoryReward("安心值", 12, "❤"),
            StoryReward("陪伴值", 8, "✦"),
            StoryReward("微光值", 5, "◎"),
        ]
        return MiniGameState(
            story_title=profile["story_title"],
            subtitle=profile["subtitle"],
            theme_subject=profile["theme_subject"],
            theme_mood=profile["theme_mood"],
            theme_style=profile["theme_style"],
            node_index=1,
            nodes=nodes,
            choices=choices,
            clues=clues,
            rewards=rewards,
            emotion_summary=profile["emotion_summary"],
        )

    def load_cached_story(self, emotion_state: EmotionState) -> Optional[MiniGameState]:
        path = self._cache_path(emotion_state)
        if not path.exists() or path.stat().st_size <= 0:
            return None
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            return self._state_from_payload(raw, emotion_state)
        except Exception:
            return None

    def cache_story(self, emotion_state: EmotionState, state: MiniGameState) -> None:
        path = self._cache_path(emotion_state)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = self._state_to_payload(state)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _state_from_text(self, text: str, emotion_state: EmotionState) -> MiniGameState:
        payload = self._parse_payload(text)
        return self._state_from_payload(payload, emotion_state)

    def _state_from_payload(self, payload: Mapping, emotion_state: EmotionState) -> MiniGameState:
        fallback = self.build_local_story(emotion_state)
        nodes = _normalize_nodes(payload.get("nodes", []), fallback.nodes)
        choices = _normalize_choices(payload.get("choices", []), fallback.choices)
        clues = _normalize_clues(payload.get("clues", []), fallback.clues)
        rewards = _normalize_rewards(payload.get("rewards", []), fallback.rewards)
        return MiniGameState(
            story_title=_clean_text(payload.get("story_title"), fallback.story_title, 18),
            subtitle=_clean_text(payload.get("subtitle"), fallback.subtitle, 28),
            theme_subject=_clean_text(payload.get("theme_subject"), fallback.theme_subject),
            theme_mood=_clean_text(payload.get("theme_mood"), fallback.theme_mood),
            theme_style=_clean_text(payload.get("theme_style"), fallback.theme_style),
            node_index=1,
            nodes=nodes,
            choices=choices,
            clues=clues,
            rewards=rewards,
            emotion_summary=_clean_text(payload.get("emotion_summary"), fallback.emotion_summary, 32),
        )

    def _state_to_payload(self, state: MiniGameState) -> Dict:
        return {
            "story_title": state.story_title,
            "subtitle": state.subtitle,
            "emotion_summary": state.emotion_summary,
            "theme_subject": state.theme_subject,
            "theme_mood": state.theme_mood,
            "theme_style": state.theme_style,
            "nodes": [node.__dict__ for node in state.nodes],
            "choices": [choice.__dict__ for choice in state.choices],
            "clues": [clue.__dict__ for clue in state.clues],
            "rewards": [reward.__dict__ for reward in state.rewards],
            "node_index": state.node_index,
            "interaction_done": state.interaction_done,
            "selected_choice_id": state.selected_choice_id,
        }

    def _parse_payload(self, text: str) -> Dict:
        raw = _strip_code_fences(text)
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            raise RuntimeError("Story response must be a JSON object")
        return parsed

    def _cache_key(self, emotion_state: EmotionState) -> str:
        raw = f"{emotion_state.emotion}|{emotion_state.label_zh}|{emotion_state.confidence:.2f}|{emotion_state.message}"
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]

    def _cache_path(self, emotion_state: EmotionState) -> Path:
        return self.cache_dir / f"story-{self._cache_key(emotion_state)}.json"


def build_story_generation_service(base_dir: Path, env_path: Optional[Path] = None) -> StoryGenerationService:
    config = load_story_generation_config(env_path=env_path)
    client = None
    if config.api_key:
        client = DeepSeekStoryClient(api_key=config.api_key, model=config.model, timeout=config.timeout)
    return StoryGenerationService(client, base_dir / "generated_stories" / "storygen")


def _strip_code_fences(text: str) -> str:
    clean = str(text).strip()
    if clean.startswith("```"):
        clean = re.sub(r"^```(?:json)?\s*", "", clean, flags=re.IGNORECASE)
        clean = re.sub(r"\s*```$", "", clean)
    start = clean.find("{")
    end = clean.rfind("}")
    if start >= 0 and end > start:
        return clean[start : end + 1]
    return clean


def _clean_text(value: object, fallback: str, max_length: Optional[int] = None) -> str:
    text = str(value).strip() if value is not None else fallback
    if not text:
        text = fallback
    if max_length is not None:
        return text[:max_length]
    return text


def _normalize_nodes(items: Sequence[Mapping], fallback_nodes: Sequence[StoryNode]) -> Sequence[StoryNode]:
    normalized = []
    for index in range(6):
        source = items[index] if index < len(items) and isinstance(items[index], Mapping) else {}
        fallback = fallback_nodes[index]
        normalized.append(
            StoryNode(
                id=_clean_text(source.get("id"), fallback.id, 32),
                title=_clean_text(source.get("title"), fallback.title, 24),
                prompt=_clean_text(source.get("prompt"), fallback.prompt, 96),
                scene_text=_clean_text(source.get("scene_text"), fallback.scene_text, 120),
                pet_reply=_clean_text(source.get("pet_reply"), fallback.pet_reply, 80),
                step_label=_clean_text(source.get("step_label"), fallback.step_label, 12),
            )
        )
    return normalized


def _normalize_choices(items: Sequence[Mapping], fallback_choices: Sequence[StoryChoice]) -> Sequence[StoryChoice]:
    normalized = []
    for index in range(3):
        source = items[index] if index < len(items) and isinstance(items[index], Mapping) else {}
        fallback = fallback_choices[index]
        normalized.append(
            StoryChoice(
                id=_clean_text(source.get("id"), fallback.id, 32),
                icon=_clean_text(source.get("icon"), fallback.icon, 8),
                title=_clean_text(source.get("title"), fallback.title, 26),
                next_node=2,
                clue_id=_clean_text(source.get("clue_id"), fallback.clue_id, 32),
            )
        )
    return normalized


def _normalize_clues(items: Sequence[Mapping], fallback_clues: Sequence[StoryClue]) -> Sequence[StoryClue]:
    normalized = []
    for index in range(6):
        source = items[index] if index < len(items) and isinstance(items[index], Mapping) else {}
        fallback = fallback_clues[index]
        collected = bool(source.get("collected")) if index < 3 else False
        normalized.append(
            StoryClue(
                id=_clean_text(source.get("id"), fallback.id, 32),
                icon=_clean_text(source.get("icon"), fallback.icon, 8),
                title=_clean_text(source.get("title"), fallback.title, 26),
                collected=collected if index >= 3 else True,
            )
        )
    return normalized


def _normalize_rewards(items: Sequence[Mapping], fallback_rewards: Sequence[StoryReward]) -> Sequence[StoryReward]:
    normalized = []
    for index in range(3):
        source = items[index] if index < len(items) and isinstance(items[index], Mapping) else {}
        fallback = fallback_rewards[index]
        value = source.get("value", fallback.value)
        try:
            value = int(value)
        except (TypeError, ValueError):
            value = fallback.value
        normalized.append(
            StoryReward(
                label=_clean_text(source.get("label"), fallback.label, 20),
                value=value,
                icon=_clean_text(source.get("icon"), fallback.icon, 8),
            )
        )
    return normalized


def _emotion_profile(emotion_state: EmotionState) -> Dict[str, str]:
    emotion = emotion_state.emotion
    if emotion in {"sad", "angry", "fear", "disgust"}:
        return {
            "story_title": "雾里的暖邮局",
            "subtitle": "先把情绪放稳，再慢慢往前走",
            "emotion_summary": "当前更需要安抚和小成功感。",
            "theme_subject": "一封会发热的信",
            "theme_mood": "安静、温柔、慢慢回暖",
            "theme_style": "治愈系 / 低压 / 轻剧情",
        }
    if emotion in {"happy", "surprise"}:
        return {
            "story_title": "风铃边的小邮局",
            "subtitle": "把轻快和惊喜留给这一局",
            "emotion_summary": "当前适合探索和奖励。",
            "theme_subject": "一封会发光的邀请",
            "theme_mood": "轻快、明亮、带点雀跃",
            "theme_style": "童话感 / 轻冒险 / 小奖励",
        }
    if emotion in {"neutral"}:
        return {
            "story_title": "安静邮局的小路标",
            "subtitle": "给平静一点方向感",
            "emotion_summary": "当前适合稳定推进和轻微变化。",
            "theme_subject": "一封慢慢抵达的信",
            "theme_mood": "平稳、温和、略带好奇",
            "theme_style": "舒缓系 / 轻探索 / 细节感",
        }
    return {
        "story_title": "雾中的小邮局",
        "subtitle": "先观察，再决定下一步",
        "emotion_summary": "当前适合温和陪伴和低门槛推进。",
        "theme_subject": "未寄出的回信",
        "theme_mood": "轻柔、稳定、带一点希望",
        "theme_style": "治愈系 / 细腻 / 可视化",
    }
