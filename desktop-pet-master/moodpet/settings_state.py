from dataclasses import dataclass, replace
from typing import List, Sequence


FREQUENCY_OPTIONS = [
    ("low", "低频", "每隔 8~12 分钟"),
    ("medium", "适中（推荐）", "每隔 2~5 分钟"),
    ("high", "高频", "每隔 30~90 秒"),
]

JUMP_TARGET_OPTIONS = [
    ("todo", "去待办"),
    ("games", "去小游戏"),
]

DEFAULT_CAMERA_NAMES = ["Integrated Camera", "Mock Camera"]


@dataclass(frozen=True)
class SettingsState:
    camera_enabled: bool = False
    camera_name: str = "Integrated Camera"
    voice_enabled: bool = True
    bubble_frequency: str = "medium"
    jump_target: str = "todo"
    bubble_do_not_disturb: bool = True
    privacy_enabled: bool = False
    autostart_enabled: bool = False
    version: str = "v1.0.0"


def available_cameras(names: Sequence[str] = ()) -> List[str]:
    clean_names = [str(name).strip() for name in names if str(name).strip()]
    return clean_names or list(DEFAULT_CAMERA_NAMES)


def frequency_label(key: str) -> str:
    for value, label, _ in FREQUENCY_OPTIONS:
        if value == key:
            return label
    return FREQUENCY_OPTIONS[1][1]


def frequency_description(key: str) -> str:
    for value, _, description in FREQUENCY_OPTIONS:
        if value == key:
            return description
    return FREQUENCY_OPTIONS[1][2]


def jump_target_label(key: str) -> str:
    for value, label in JUMP_TARGET_OPTIONS:
        if value == key:
            return label
    return JUMP_TARGET_OPTIONS[0][1]


def camera_status_text(state: SettingsState) -> str:
    return "摄像头已开启" if state.camera_enabled else "摄像头已关闭"


def privacy_status_text(state: SettingsState) -> str:
    return "隐私模式已开启" if state.privacy_enabled else "隐私模式已关闭"


def voice_status_text(state: SettingsState) -> str:
    return "语音功能已开启" if state.voice_enabled else "语音功能已关闭"


def autostart_status_text(state: SettingsState) -> str:
    return "开机自启动已开启" if state.autostart_enabled else "开机自启动已关闭"


def apply_camera_selection(state: SettingsState, camera_name: str, names: Sequence[str]) -> SettingsState:
    cameras = available_cameras(names)
    selected = camera_name if camera_name in cameras else cameras[0]
    return replace(state, camera_name=selected)


def apply_frequency(state: SettingsState, frequency: str) -> SettingsState:
    valid_values = {value for value, _, _ in FREQUENCY_OPTIONS}
    return replace(state, bubble_frequency=frequency if frequency in valid_values else "medium")


def apply_jump_target(state: SettingsState, target: str) -> SettingsState:
    valid_values = {value for value, _ in JUMP_TARGET_OPTIONS}
    return replace(state, jump_target=target if target in valid_values else "todo")
