from typing import Dict, List, Mapping, Sequence

from moodpet.bubble_policy import BubbleContext, BubbleSettings, build_bubble_reply
from moodpet.emotion import EmotionState


ACTIVE_BUBBLES = {
    "happy": "今天状态不错！来玩一局吗？",
    "neutral": "我在旁边待机，随时陪你开始。",
    "surprise": "好像有新发现，要不要记录一下？",
    "sad": "你看起来有点累，要不要先完成一个小任务？",
    "angry": "先暂停一下，喝口水再继续也可以。",
    "disgust": "状态不太舒服，换个轻松任务缓一缓吧。",
    "fear": "别急，我陪你一步一步来。",
    "away": "暂时没有看到你，回来后我继续陪你。",
    "unknown": "状态感知中，我会轻轻陪着你。",
    "disabled": "状态感知未开启，右键可以开启陪伴感知。",
    "error": "状态感知暂不可用，可能需要检查权限或占用。",
}


def camera_status_text(enabled: bool, emotion: str = "") -> str:
    if not enabled:
        return "状态感知：未开启"
    if emotion == "error":
        return "状态感知：暂不可用"
    return "状态感知中"


def pet_bubble_text(state: EmotionState) -> str:
    if state.emotion in {"disabled", "error"}:
        return ACTIVE_BUBBLES.get(state.emotion, ACTIVE_BUBBLES["unknown"])
    context = BubbleContext(emotion_state=state, settings=BubbleSettings())
    return build_bubble_reply(context).text


def should_open_navigation(click_count: int, dragged: bool) -> bool:
    return click_count >= 2 and not dragged


def build_navigation_groups(menu_config: Mapping[str, Sequence[Dict]]) -> List[Dict]:
    groups = []
    for title, items in menu_config.items():
        groups.append(
            {
                "title": str(title),
                "items": [dict(item) for item in items],
            }
        )
    return groups


def build_feature_modules(menu_config: Mapping[str, Sequence[Dict]], emotion_enabled: bool = False) -> List[Dict]:
    action_count = sum(len(items) for items in menu_config.values())
    camera_title = "关闭感知" if emotion_enabled else "开启感知"
    camera_description = "状态感知正在轻量运行" if emotion_enabled else "开启本地状态感知"

    return [
        {
            "id": "realtime",
            "title": "实时检测",
            "icon": "≋",
            "icon_feature": "realtime",
            "description": camera_description,
            "cta": camera_title,
            "accent": "mint",
        },
        {
            "id": "todo",
            "title": "待办",
            "icon": "☑",
            "icon_feature": "todo",
            "description": f"{action_count} 个快捷功能",
            "cta": "打开清单",
            "accent": "pink",
        },
        {
            "id": "games",
            "title": "小游戏",
            "icon": "✦",
            "icon_feature": "games",
            "description": "启动轻量休息入口",
            "cta": "开始放松",
            "accent": "lilac",
        },
        {
            "id": "settings",
            "title": "设置",
            "icon": "⚙",
            "icon_feature": "settings",
            "description": "管理菜单与脚本",
            "cta": "打开配置",
            "accent": "sky",
        },
    ]
