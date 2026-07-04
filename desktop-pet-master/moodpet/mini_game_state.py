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


def build_default_game() -> MiniGameState:
    nodes = [
        StoryNode(
            "opening",
            "开场",
            "黄昏的小邮局亮起灯，你听见柜台里传来轻轻的纸页声。",
            "雾气贴着窗，邮局的灯像一颗慢慢醒来的星星。",
            "我们先靠近看看，别把线索吓跑。",
            "开场",
        ),
        StoryNode(
            "event",
            "事件节点 02",
            "你发现了这封信，接下来要做什么呢？",
            "黄昏的邮局里，一封没有署名的信从柜台边悄悄滑落。楼上的钟慢了半拍，像在等谁回信。",
            "我会陪你把这封信读完。",
            "事件",
        ),
        StoryNode(
            "pet",
            "MoodPet 的嗅闻",
            "MoodPet 闻到信封边缘有一阵薄荷香，像是从旧书页里跑出来的。",
            "你把信交给 MoodPet，它绕着信封转了两圈，尾巴轻轻敲着木地板。",
            "这味道很轻，我们记下来。",
            "选择",
        ),
        StoryNode(
            "sealed",
            "封好的回信",
            "线索已经整理好，把散落的信纸放回信封里吧。",
            "信纸归位后，邮局门口的风铃响了一下，像有人终于收到了回信。",
            "不急，我们先看最轻的线索。",
            "线索",
        ),
        StoryNode(
            "ending",
            "结尾",
            "雾散开了，小邮局把最后一封信送进了夜色。",
            "蓝色邮票、慢半拍的钟声、薄荷香和回信日期拼在一起，指向一个温柔的误会。",
            "故事完成啦，今天也有好好陪伴彼此。",
            "结尾",
        ),
    ]
    return MiniGameState(
        story_title="雾中的小邮局",
        subtitle="根据当前状态生成的互动故事",
        theme_subject="未寄出的回信",
        theme_mood="黄昏、微风、纸页声",
        theme_style="轻异常 / 隐喻",
        node_index=1,
        nodes=nodes,
        choices=[
            StoryChoice("pick_letter", "✉", "捡起那封信", 3, "return_date"),
            StoryChoice("clock", "◷", "先看看停摆的钟", 3, "clock_note"),
            StoryChoice("ask_pet", "🐾", "让 MoodPet 闻一问信纸", 2, "mint_scent"),
        ],
        clues=[
            StoryClue("stamp", "▣", "蓝色邮票", True),
            StoryClue("clock", "◷", "慢半拍的钟声", True),
            StoryClue("address", "□", "未写完的地址", True),
            StoryClue("mint_scent", "♧", "信封边缘的薄荷香", False),
            StoryClue("return_date", "◇", "回信日期", False),
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
    if state.interaction_done or state.node_index >= 3:
        return []
    return list(state.choices)


def choose_event(state: MiniGameState, choice_id: str) -> MiniGameState:
    match = next((choice for choice in state.choices if choice.id == choice_id), None)
    if match is None:
        return state
    clues = _collect_clue(state.clues, match.clue_id)
    return replace(state, node_index=match.next_node, clues=clues)


def complete_interaction(state: MiniGameState) -> MiniGameState:
    clues = _collect_clue(_collect_clue(state.clues, "return_date"), "mint_scent")
    return replace(state, node_index=3, clues=clues, interaction_done=True)


def restart_game(state: MiniGameState | None = None) -> MiniGameState:
    return build_default_game()


def _collect_clue(clues: Sequence[StoryClue], clue_id: str) -> List[StoryClue]:
    return [replace(clue, collected=True) if clue.id == clue_id else clue for clue in clues]
