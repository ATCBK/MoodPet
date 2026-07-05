import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable, Dict, Mapping, Optional

from moodpet.bubble_policy import (
    BubblePrompt,
    BubbleReplyProvider,
    LocalRuleBubbleProvider,
    ModelBubbleProvider,
)


DEEPSEEK_CHAT_COMPLETIONS_URL = "https://api.deepseek.com/chat/completions"
DEFAULT_DEEPSEEK_MODEL = "deepseek-v4-flash"
DEFAULT_TIMEOUT_SECONDS = 3.0


JsonPostFunc = Callable[[str, Dict, Dict[str, str], float], Dict]


def load_env_file(source: object) -> Dict[str, str]:
    if isinstance(source, (str, bytes)):
        text = source.decode("utf-8") if isinstance(source, bytes) else source
    else:
        path = Path(source)
        if not path.exists():
            return {}
        text = path.read_text(encoding="utf-8")

    values: Dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def post_json(url: str, payload: Dict, headers: Dict[str, str], timeout: float) -> Dict:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw_body = response.read().decode("utf-8")
    except urllib.error.URLError as exc:
        raise RuntimeError("DeepSeek request failed") from exc

    try:
        decoded = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise RuntimeError("DeepSeek returned invalid JSON") from exc
    if not isinstance(decoded, dict):
        raise RuntimeError("DeepSeek returned an invalid response")
    return decoded


class DeepSeekBubbleClient:
    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_DEEPSEEK_MODEL,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        post_json: JsonPostFunc = post_json,
    ) -> None:
        self.api_key = api_key
        self.model = model or DEFAULT_DEEPSEEK_MODEL
        self.timeout = timeout
        self.post_json = post_json

    def complete(self, prompt: BubblePrompt) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self._system_message(prompt)},
                {"role": "user", "content": self._user_message(prompt)},
            ],
            "thinking": {"type": "disabled"},
            "temperature": 0.92,
            "presence_penalty": 0.8,
            "frequency_penalty": 0.8,
            "max_tokens": 48,
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

    def _system_message(self, prompt: BubblePrompt) -> str:
        return (
            "你是 MoodPet 桌宠的气泡文案引擎。"
            f"{prompt.style_rule}"
            f"{prompt.safety_rule}"
            f"每次生成必须不同，不要重复上一条：{prompt.recent_reply or '无'}。"
            f"只输出一句中文，最多 {prompt.max_length} 个汉字或字符，不要解释。"
        )

    def _user_message(self, prompt: BubblePrompt) -> str:
        confidence_percent = int(round(prompt.confidence * 100))
        return (
            f"当前情绪：{prompt.label_zh}（{prompt.emotion}），置信度 {confidence_percent}%。"
            f"推荐跳转目标：{prompt.target_id}。"
            "请生成一条适合桌宠主动弹出的短提醒。"
        )

    @staticmethod
    def _extract_text(response: Mapping) -> str:
        try:
            content = response["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("DeepSeek response missing message content") from exc
        return str(content).strip()


def build_default_bubble_provider(
    env_values: Optional[Mapping[str, str]] = None,
    env_path: Optional[Path] = None,
) -> BubbleReplyProvider:
    file_values = load_env_file(env_path) if env_path is not None else {}
    values = {**file_values, **(env_values or {}), **os.environ}
    api_key = values.get("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        return LocalRuleBubbleProvider()

    model = values.get("DEEPSEEK_MODEL", DEFAULT_DEEPSEEK_MODEL).strip() or DEFAULT_DEEPSEEK_MODEL
    client = DeepSeekBubbleClient(api_key=api_key, model=model)
    return ModelBubbleProvider(client, fallback=LocalRuleBubbleProvider())
