import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Mapping, Optional

from moodpet.deepseek_bubble import load_env_file
from moodpet.mini_game_state import (
    MiniGameState,
    StoryChoice,
    build_choice_image_prompt,
    build_node_image_prompt,
    current_node,
)


DEFAULT_ARK_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
DEFAULT_SEEDREAM_MODEL = "doubao-seedream-5-0-260128"
DEFAULT_SEEDREAM_SIZE = "2K"
DEFAULT_TIMEOUT_SECONDS = 90.0


JsonPostFunc = Callable[[str, Dict, Dict[str, str], float], Dict]
DownloadFunc = Callable[[str, Dict[str, str], float], bytes]


@dataclass(frozen=True)
class SeedreamConfig:
    api_key: str
    base_url: str = DEFAULT_ARK_BASE_URL
    model: str = DEFAULT_SEEDREAM_MODEL
    size: str = DEFAULT_SEEDREAM_SIZE
    watermark: bool = False
    timeout: float = DEFAULT_TIMEOUT_SECONDS

    @property
    def endpoint(self) -> str:
        return self.base_url.rstrip("/") + "/images/generations"


def _bool_value(value: object, default: bool = False) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def load_seedream_config(values: Optional[Mapping[str, str]] = None, env_path: Optional[Path] = None) -> SeedreamConfig:
    file_values = load_env_file(env_path) if env_path is not None else {}
    merged = {**file_values, **(values or {}), **os.environ}
    timeout = float(merged.get("SEEDREAM_TIMEOUT", DEFAULT_TIMEOUT_SECONDS))
    return SeedreamConfig(
        api_key=merged.get("ARK_API_KEY", "").strip(),
        base_url=merged.get("ARK_BASE_URL", DEFAULT_ARK_BASE_URL).strip() or DEFAULT_ARK_BASE_URL,
        model=merged.get("SEEDREAM_MODEL_ID", DEFAULT_SEEDREAM_MODEL).strip() or DEFAULT_SEEDREAM_MODEL,
        size=merged.get("SEEDREAM_DEFAULT_SIZE", DEFAULT_SEEDREAM_SIZE).strip() or DEFAULT_SEEDREAM_SIZE,
        watermark=_bool_value(merged.get("SEEDREAM_DEFAULT_WATERMARK"), False),
        timeout=timeout,
    )


def post_json(url: str, payload: Dict, headers: Dict[str, str], timeout: float) -> Dict:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw_body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Seedream request failed: HTTP {exc.code} {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError("Seedream request failed") from exc
    try:
        decoded = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Seedream returned invalid JSON") from exc
    if not isinstance(decoded, dict):
        raise RuntimeError("Seedream returned an invalid response")
    return decoded


def download_bytes(url: str, headers: Dict[str, str], timeout: float) -> bytes:
    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read()
    except urllib.error.URLError as exc:
        raise RuntimeError("Seedream image download failed") from exc


class SeedreamImageClient:
    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_ARK_BASE_URL,
        model: str = DEFAULT_SEEDREAM_MODEL,
        size: str = DEFAULT_SEEDREAM_SIZE,
        watermark: bool = False,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        post_json: JsonPostFunc = post_json,
        download: DownloadFunc = download_bytes,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model or DEFAULT_SEEDREAM_MODEL
        self.size = size or DEFAULT_SEEDREAM_SIZE
        self.watermark = watermark
        self.timeout = timeout
        self.post_json = post_json
        self.download = download

    @property
    def endpoint(self) -> str:
        return self.base_url + "/images/generations"

    def generate_image_url(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "response_format": "url",
            "size": self.size,
            "watermark": self.watermark,
        }
        response = self.post_json(self.endpoint, payload, self._headers(), self.timeout)
        return self._extract_url(response)

    def download_image(self, url: str) -> bytes:
        return self.download(url, self._headers(), self.timeout)

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _extract_url(response: Mapping) -> str:
        try:
            url = response["data"][0]["url"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("Seedream response missing image url") from exc
        if not str(url).strip():
            raise RuntimeError("Seedream returned empty image url")
        return str(url).strip()


class SeedreamImageService:
    def __init__(self, client: SeedreamImageClient, cache_dir: Path) -> None:
        self.client = client
        self.cache_dir = cache_dir

    def ensure_choice_image(self, state: MiniGameState, choice: StoryChoice) -> Path:
        prompt = build_choice_image_prompt(state, choice)
        path = self._cache_path(state, choice, prompt)
        if path.exists() and path.stat().st_size > 0:
            return path
        path.parent.mkdir(parents=True, exist_ok=True)
        image_url = self.client.generate_image_url(prompt)
        path.write_bytes(self.client.download_image(image_url))
        return path

    def ensure_node_image(self, state: MiniGameState) -> Path:
        prompt = build_node_image_prompt(state)
        path = self._node_cache_path(state, prompt)
        if path.exists() and path.stat().st_size > 0:
            return path
        path.parent.mkdir(parents=True, exist_ok=True)
        image_url = self.client.generate_image_url(prompt)
        path.write_bytes(self.client.download_image(image_url))
        return path

    def _cache_path(self, state: MiniGameState, choice: StoryChoice, prompt: str) -> Path:
        digest = hashlib.sha1(prompt.encode("utf-8")).hexdigest()[:12]
        safe_story = _safe_slug(state.story_title)
        safe_choice = _safe_slug(choice.id)
        return self.cache_dir / safe_story / f"{state.node_index}-{safe_choice}-{digest}.png"

    def _node_cache_path(self, state: MiniGameState, prompt: str) -> Path:
        digest = hashlib.sha1(prompt.encode("utf-8")).hexdigest()[:12]
        safe_story = _safe_slug(state.story_title)
        safe_node = _safe_slug(current_node(state).id)
        return self.cache_dir / safe_story / f"node-{state.node_index}-{safe_node}-{digest}.png"


def _safe_slug(value: str) -> str:
    clean = re.sub(r"[^0-9A-Za-z_-]+", "-", value).strip("-")
    return clean or "story"


def build_seedream_image_service(base_dir: Path, env_path: Optional[Path] = None) -> Optional[SeedreamImageService]:
    config = load_seedream_config(env_path=env_path)
    if not config.api_key:
        return None
    client = SeedreamImageClient(
        api_key=config.api_key,
        base_url=config.base_url,
        model=config.model,
        size=config.size,
        watermark=config.watermark,
        timeout=config.timeout,
    )
    return SeedreamImageService(client, base_dir / "generated_images" / "seedream")
