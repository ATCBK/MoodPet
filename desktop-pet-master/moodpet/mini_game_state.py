from dataclasses import dataclass, replace
from typing import Dict, List, Sequence


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


BRANCH_NODE_OVERRIDES: Dict[str, Dict[int, StoryNode]] = {
    "pick_letter": {
        2: StoryNode(
            "letter_date",
            "回信背面的日期",
            "你把信封翻到背面，先确认旧邮戳和日期。",
            "旧蜡封旁露出一行很浅的日期。那不是退信标记，而像是寄信人刻意留下的提醒。",
            "日期还没有过期，这封信是在等一个愿意把它送完的人。",
            "选择",
        ),
        3: StoryNode(
            "letter_seal",
            "旧蜡封的保存痕迹",
            "你检查蜡封、折痕和纸页边缘，判断这封信被谁保存过。",
            "蜡封边缘没有被拆开的痕迹，纸角却被反复抚平。有人舍不得寄出，也舍不得丢掉。",
            "它被认真保护过，所以我们也要认真对待它。",
            "线索",
        ),
        4: StoryNode(
            "letter_address",
            "补全回信地址",
            "你把日期、邮票和未写完的地址连起来，确认投递方向。",
            "蓝色邮票上的旧街区编号，正好补上地址最后缺失的两格。柜台后的地图慢慢亮起一条短短的路。",
            "找到啦，不是远方，是邮局转角那盏灯下面。",
            "行动",
        ),
        5: StoryNode(
            "letter_ending",
            "雾散后的投递",
            "你按补全的地址，把迟到的回信交到正确的门前。",
            "门缝里透出暖光，回信安静地落进信箱。风铃响了一下，像有人终于等到那句话。",
            "这条路线完成啦，温柔的事情也需要被送达。",
            "结尾",
        ),
    },
    "clock": {
        2: StoryNode(
            "clock_signal",
            "钟声里的暗号",
            "你抬头观察停摆的钟，确认它为什么总慢半拍。",
            "钟针停在黄昏后的第三格，每一次慢半拍都会让柜台里的纸页轻轻翻动。",
            "它不是坏了，是在提醒我们听见被错过的时间。",
            "选择",
        ),
        3: StoryNode(
            "clock_mailbox",
            "亮起的信箱格",
            "你顺着钟声看向信箱格，找出被它点亮的位置。",
            "钟声落下时，第三排第二格的信箱短暂发亮。里面有一张旧便签，记录着最后一次投递失败的原因。",
            "原来信没有丢，是时间把它暂时藏起来了。",
            "线索",
        ),
        4: StoryNode(
            "clock_direction",
            "确认投递方向",
            "你把便签、钟声和邮票编号连起来，确认下一步投递方向。",
            "便签上的路线和钟面的刻度重合，指向雾里那条只在整点前出现的小巷。",
            "我们要赶在下一次钟声之前，把它送过去。",
            "行动",
        ),
        5: StoryNode(
            "clock_ending",
            "雾散后的投递",
            "你按照钟声给出的时间，把回信送进雾中的小巷。",
            "整点前，蓝色信箱在雾里亮了一瞬。回信落下后，慢半拍的钟终于轻轻追上了时间。",
            "这条路线完成啦，有些等待只是差一个准点抵达。",
            "结尾",
        ),
    },
    "ask_pet": {
        2: StoryNode(
            "pet_scent",
            "薄荷香的方向",
            "MoodPet 贴近信纸，顺着薄荷香寻找来源。",
            "薄荷香从信封边缘亮起，绕过柜台、旧书架和蓝色邮筒，像一条很轻的线。",
            "味道不会说谎，我们跟着它慢慢走。",
            "选择",
        ),
        3: StoryNode(
            "pet_address_book",
            "旧书架旁的通讯录",
            "你和 MoodPet 在旧书架旁停下，查看那本被风翻开的通讯录。",
            "通讯录停在一页被压弯的纸上，名字旁边夹着一片干薄荷叶，地址只缺最后一行。",
            "这不是普通香味，是寄信人留下的记号。",
            "线索",
        ),
        4: StoryNode(
            "pet_direction",
            "确认投递方向",
            "你把通讯录、薄荷叶和未写完的地址连起来，确认投递方向。",
            "MoodPet 用爪子轻轻点住地图边缘。那里的街灯旁，有一间总在黄昏煮薄荷茶的小屋。",
            "我记住这股味道了，我们不会走错。",
            "行动",
        ),
        5: StoryNode(
            "pet_ending",
            "雾散后的投递",
            "你跟着薄荷香，把迟到的回信送到黄昏里的小屋。",
            "门前的薄荷盆被风吹得轻轻晃动。回信放进信箱后，MoodPet 的尾巴也跟着亮了一下。",
            "这条路线完成啦，气味把想念带回了家。",
            "结尾",
        ),
    },
}


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
            "choice_result",
            "选择后的线索",
            "你的选择让邮局里的某个细节亮了起来。",
            "你刚刚关注的线索在暖光里轻轻发亮，像是在回应这一步。",
            "这一幕记住了你的选择，我们继续往下看。",
            "选择",
        ),
        StoryNode(
            "clue_trace",
            "线索展开",
            "线索变得更清楚了，需要继续整理它和回信之间的关系。",
            "柜台、信箱和旧地图之间出现了新的联系，故事正从一个细节扩展成一条路径。",
            "别急，我们已经接近真正的去处了。",
            "线索",
        ),
        StoryNode(
            "action",
            "确认投递方向",
            "把目前的线索串起来，确认这封回信应该被送到哪里。",
            "所有线索在邮局地图上慢慢合拢，指向雾里一处温暖的灯光。",
            "路线出现了，我们准备出发。",
            "行动",
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
            StoryChoice("clock", "◷", "先看看停摆的钟", 2, "clock_note"),
            StoryChoice("ask_pet", "🐾", "让 MoodPet 闻一问信纸", 2, "mint_scent"),
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
    index = max(0, min(state.node_index, len(state.nodes) - 1))
    branch_nodes = BRANCH_NODE_OVERRIDES.get(state.selected_choice_id, {})
    return branch_nodes.get(index, state.nodes[index])


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
        "pixel art, cozy game item illustration, cozy game choice card, MoodPet desktop pet adventure, "
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
        f"Story title: {state.story_title}. Route: {state.selected_choice_id or 'not selected'}. Chapter: {node.title}. "
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
        return replace(state, node_index=state.node_index + 1, interaction_done=True)
    return state


def complete_interaction(state: MiniGameState) -> MiniGameState:
    clues = _collect_clue(_collect_clue(state.clues, "return_date"), "mint_scent")
    clues = _collect_clue(clues, "clock_note")
    return replace(state, node_index=len(state.nodes) - 1, clues=clues, interaction_done=True)


def restart_game(state: MiniGameState | None = None) -> MiniGameState:
    return build_default_game()


def _collect_clue(clues: Sequence[StoryClue], clue_id: str) -> List[StoryClue]:
    return [replace(clue, collected=True) if clue.id == clue_id else clue for clue in clues]
