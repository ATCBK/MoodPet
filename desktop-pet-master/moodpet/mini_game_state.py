from dataclasses import dataclass, replace
from typing import List, Sequence


@dataclass(frozen=True)
class StoryNode:
    id: str
    title: str
    prompt: str
    scene_text: str
    pet_reply: str
    step_label: str


@dataclass(frozen=True)
class StoryChoice:
    id: str
    icon: str
    title: str
    next_node: int
    clue_id: str


@dataclass(frozen=True)
class StoryClue:
    id: str
    icon: str
    title: str
    collected: bool = False


@dataclass(frozen=True)
class StoryReward:
    label: str
    value: int
    icon: str


@dataclass(frozen=True)
class MiniGameState:
    story_title: str
    subtitle: str
    theme_subject: str
    theme_mood: str
    theme_style: str
    node_index: int
    nodes: Sequence[StoryNode]
    choices: Sequence[StoryChoice]
    clues: Sequence[StoryClue]
    rewards: Sequence[StoryReward]
    interaction_done: bool = False
    selected_choice_id: str = ""


def build_default_game() -> MiniGameState:
    nodes = [
        StoryNode(
            "opening",
            "开场",
            "黄昏的小邮局亮起灯，你听见柜台里传来轻轻的纸页声。",
            "雾气贴着窗，小邮局的灯像一颗慢慢醒来的星星。",
            "我们先靠近看看，别把线索吓跑。",
            "开场",
        ),
        StoryNode(
            "event",
            "事件节点 02",
            "你发现了一封没有署名的回信，接下来要先确认哪条线索？",
            "黄昏的邮局里，一封没有署名的信从柜台边悄悄滑落。楼上的钟慢了半拍，信封边缘还有很淡的薄荷香。",
            "我会陪你把这封信读完，但第一步要选得仔细。",
            "事件",
        ),
        StoryNode(
            "letter_branch",
            "无署名的回信",
            "你捡起信，先检查信封背面和邮戳。",
            "信封翻到背面时，旧蜡封旁露出一行浅浅的日期。它不是普通退信，而是一封被人认真保存过的回信。",
            "这封信不是丢失，它是在等一个愿意把它送完的人。",
            "分支",
        ),
        StoryNode(
            "clock_branch",
            "慢半拍的钟",
            "你抬头观察停摆的钟，确认它为什么总慢半拍。",
            "钟针在旧邮局里轻轻停顿，分针每次跳动都会让信箱格亮起一瞬。那半拍像是某个约定留下的暗号。",
            "它不是坏了，是在替某封信保留最后一分钟。",
            "分支",
        ),
        StoryNode(
            "pet_branch",
            "薄荷香的方向",
            "MoodPet 贴近信纸，顺着薄荷香寻找来源。",
            "薄荷香从信封边缘亮起，绕过柜台、旧书架和蓝色邮筒，最后停在一本被风翻开的通讯录旁。",
            "味道指向旧书架，我们找到它留下的温柔痕迹。",
            "分支",
        ),
        StoryNode(
            "ending",
            "雾散后的投递",
            "线索被串起来，迟到的回信终于有了去处。",
            "夜色里，小邮局把那封迟到的回信送到灯下。雾散开后，门口的风铃响了一下，像有人轻轻说了谢谢。",
            "故事完成啦，今天也有好好陪伴彼此。",
            "结尾",
        ),
    ]
    return MiniGameState(
        story_title="雾中的小邮局",
        subtitle="根据当前状态生成的互动故事",
        theme_subject="未寄出的回信",
        theme_mood="黄昏、微风、纸页声",
        theme_style="轻异想 / 隐喻",
        node_index=1,
        nodes=nodes,
        choices=[
            StoryChoice("pick_letter", "✉", "捡起那封信", 2, "return_date"),
            StoryChoice("clock", "◷", "先看看停摆的钟", 3, "clock_note"),
            StoryChoice("ask_pet", "🐾", "让 MoodPet 闻一问信纸", 4, "mint_scent"),
        ],
        clues=[
            StoryClue("stamp", "▣", "蓝色邮票", True),
            StoryClue("clock", "◷", "慢半拍的钟声", True),
            StoryClue("address", "?", "未写完的地址", True),
            StoryClue("mint_scent", "♡", "信封边缘的薄荷香", False),
            StoryClue("return_date", "◉", "回信日期", False),
            StoryClue("clock_note", "◌", "钟针暗号", False),
        ],
        rewards=[
            StoryReward("宠物经验", 12, "✿"),
            StoryReward("陪伴值", 8, "♥"),
            StoryReward("灵感值", 5, "☼"),
        ],
    )


def current_node(state: MiniGameState) -> StoryNode:
    return state.nodes[max(0, min(state.node_index, len(state.nodes) - 1))]


def progress_text(state: MiniGameState) -> str:
    return f"流程 {state.node_index + 1}/{len(state.nodes)}"


def collected_count_text(state: MiniGameState) -> str:
    collected = sum(1 for clue in state.clues if clue.collected)
    return f"{collected} / {len(state.clues)}"


def available_choices(state: MiniGameState) -> List[StoryChoice]:
    if state.interaction_done or state.node_index != 1:
        return []
    return list(state.choices)


def build_choice_image_prompt(state: MiniGameState, choice: StoryChoice) -> str:
    node = current_node(state)
    return (
        "pixel art, cozy game choice card, MoodPet desktop pet adventure, "
        "soft chunky pixels, warm outline, readable small game card, no text, no watermark, "
        f"story title: {state.story_title}, theme: {state.theme_subject}, "
        f"mood: {state.theme_mood}, style: {state.theme_style}, "
        f"current scene: {node.scene_text}, player choice: {choice.title}, "
        "create one square 2D pixel-game illustration matching the MoodPet brand."
    )


def build_node_image_prompt(state: MiniGameState) -> str:
    node = current_node(state)
    return (
        "Use case: illustration-story. Asset type: MoodPet mini-game chapter image. "
        "Primary request: create a polished 2D pixel art game scene for the current story chapter. "
        "Scene/backdrop: a cozy magical postal room with warm wood, a blue mailbox, soft lantern light, and gentle fog outside. "
        "Subject: MoodPet, a small golden companion pet, helps solve a quiet postal mystery. "
        "Style/medium: premium pixel art, cozy narrative game, chunky clean pixels, warm outlines, game UI compatible. "
        "Composition/framing: landscape scene, central story object clearly visible, no text areas inside the image. "
        f"Story title: {state.story_title}. Chapter: {node.title}. "
        f"Chapter scene: {node.scene_text}. Pet reaction: {node.pet_reply}. "
        "Constraints: no text, no watermark, no logo, no photorealism, keep the mood gentle and readable at small size."
    )


def choose_event(state: MiniGameState, choice_id: str) -> MiniGameState:
    match = next((choice for choice in state.choices if choice.id == choice_id), None)
    if match is None:
        return state
    clues = _collect_clue(state.clues, match.clue_id)
    return replace(state, node_index=match.next_node, clues=clues, interaction_done=True, selected_choice_id=match.id)


def continue_story(state: MiniGameState) -> MiniGameState:
    if state.interaction_done and state.node_index < len(state.nodes) - 1:
        return replace(state, node_index=len(state.nodes) - 1, interaction_done=True)
    return state


def complete_interaction(state: MiniGameState) -> MiniGameState:
    clues = _collect_clue(_collect_clue(state.clues, "return_date"), "mint_scent")
    clues = _collect_clue(clues, "clock_note")
    return replace(state, node_index=len(state.nodes) - 1, clues=clues, interaction_done=True)


def restart_game(state: MiniGameState | None = None) -> MiniGameState:
    return build_default_game()


def _collect_clue(clues: Sequence[StoryClue], clue_id: str) -> List[StoryClue]:
    return [replace(clue, collected=True) if clue.id == clue_id else clue for clue in clues]
