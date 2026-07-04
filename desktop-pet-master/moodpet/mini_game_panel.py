from pathlib import Path
from typing import List, Optional, Tuple

from PyQt5.QtCore import QPoint, QRect, QSize, Qt
from PyQt5.QtGui import QColor, QFont, QMovie, QPainter, QPen
from PyQt5.QtWidgets import QFrame, QLabel, QPushButton, QWidget

from moodpet.mini_game_state import (
    MiniGameState,
    available_choices,
    build_default_game,
    choose_event,
    collected_count_text,
    complete_interaction,
    current_node,
    progress_text,
    restart_game,
)
from moodpet.pixel_icons import apply_button_icon, apply_label_icon


INK = "#10151b"
NAVY = "#062b36"
TEAL = "#19c4a8"
CREAM = "#fff1da"
PANEL = "#fff7e9"
LINE = "#b99169"
SOFT_LINE = "#d8b98e"
BLUE = "#247fd8"
MINT = "#18b985"
PINK = "#ff6374"
LILAC = "#d8b8ff"
GOLD = "#ffc34f"


def label(parent: QWidget, text: str, geometry: Tuple[int, int, int, int], size: int = 12, weight: int = 700) -> QLabel:
    item = QLabel(text, parent)
    item.setGeometry(*geometry)
    item.setWordWrap(True)
    item.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    item.setFont(QFont("Microsoft YaHei", size, weight))
    item.setStyleSheet(f"color: {INK}; border: none; background: transparent;")
    return item


class PixelButton(QPushButton):
    def __init__(self, text: str, parent: QWidget, color: str = PANEL, text_color: str = INK) -> None:
        super().__init__(text, parent)
        self.base_color = color
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(
            "QPushButton {"
            f"background-color: {color};"
            f"color: {text_color};"
            "border: 2px solid #8b6a4d;"
            "border-radius: 5px;"
            "padding: 7px 12px;"
            "text-align: left;"
            "}"
            "QPushButton:hover { background-color: #fffaf2; }"
            "QPushButton:pressed { padding-left: 14px; padding-top: 9px; }"
        )
        self.setFont(QFont("Microsoft YaHei", 11, 900))


class PostalScene(QWidget):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.caption = ""

    def set_caption(self, caption: str) -> None:
        self.caption = caption
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)
        rect = self.rect().adjusted(2, 2, -2, -2)
        painter.fillRect(rect, QColor("#20334c"))

        for y, color in [(0, "#8c5c80"), (44, "#d78a77"), (88, "#f3b27a"), (132, "#644e69")]:
            painter.fillRect(rect.left(), rect.top() + y, rect.width(), 48, QColor(color))

        painter.fillRect(rect.left(), rect.top() + 156, rect.width(), rect.height() - 156, QColor("#2a273a"))
        painter.fillRect(rect.left() + 26, rect.top() + 44, 220, 182, QColor("#17263a"))
        painter.fillRect(rect.left() + 38, rect.top() + 56, 196, 158, QColor("#f0a36d"))
        painter.fillRect(rect.left() + 44, rect.top() + 62, 184, 146, QColor("#6c6a95"))

        painter.setPen(QPen(QColor("#1a1724"), 5))
        painter.drawLine(rect.left() + 132, rect.top() + 54, rect.left() + 132, rect.top() + 214)
        painter.drawLine(rect.left() + 42, rect.top() + 134, rect.left() + 232, rect.top() + 134)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#503522"))
        painter.drawRect(rect.left() + 270, rect.top() + 122, 180, 194)
        painter.drawRect(rect.left() + 292, rect.top() + 82, 128, 42)
        painter.setBrush(QColor("#8c623b"))
        for row in range(4):
            for col in range(3):
                painter.drawRect(rect.left() + 288 + col * 48, rect.top() + 146 + row * 38, 36, 24)

        painter.setBrush(QColor("#ffd38a"))
        painter.drawEllipse(rect.left() + 262, rect.top() + 38, 58, 58)
        painter.setBrush(QColor("#201920"))
        painter.drawRect(rect.left() + 288, rect.top() + 8, 7, 42)

        painter.setBrush(QColor("#6b452c"))
        painter.drawRect(rect.left() + 12, rect.bottom() - 92, rect.width() - 24, 70)
        painter.setBrush(QColor("#f7e6c7"))
        painter.drawRect(rect.left() + 154, rect.bottom() - 78, 98, 54)
        painter.setPen(QPen(QColor("#c77a54"), 2))
        painter.drawLine(rect.left() + 170, rect.bottom() - 62, rect.left() + 232, rect.bottom() - 56)
        painter.drawLine(rect.left() + 170, rect.bottom() - 48, rect.left() + 216, rect.bottom() - 42)

        painter.setPen(QPen(QColor("#071927"), 4))
        painter.drawRect(rect)

        painter.fillRect(rect.left(), rect.bottom() - 86, rect.width(), 84, QColor("#fff1da"))
        painter.setPen(QColor(INK))
        painter.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        painter.drawText(QRect(rect.left() + 18, rect.bottom() - 78, rect.width() - 36, 66), Qt.AlignLeft | Qt.AlignVCenter | Qt.TextWordWrap, self.caption)


class DraggableEnvelope(QLabel):
    def __init__(self, parent: QWidget, drop_rect: QRect, on_dropped) -> None:
        super().__init__("✉", parent)
        self.drop_rect = drop_rect
        self.on_dropped = on_dropped
        self.drag_offset = QPoint(0, 0)
        self.home = QPoint(34, 52)
        self.setGeometry(self.home.x(), self.home.y(), 70, 48)
        self.setAlignment(Qt.AlignCenter)
        self.setCursor(Qt.OpenHandCursor)
        self.setStyleSheet(
            "background-color: #fffaf2; color: #d45656; border: 2px solid #b99169;"
            "border-radius: 4px; font: 900 24pt 'Microsoft YaHei';"
        )

    def reset_position(self) -> None:
        self.move(self.home)
        self.show()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.drag_offset = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()

    def mouseMoveEvent(self, event) -> None:
        if event.buttons() & Qt.LeftButton:
            self.move(self.mapToParent(event.pos() - self.drag_offset))
            event.accept()

    def mouseReleaseEvent(self, event) -> None:
        self.setCursor(Qt.OpenHandCursor)
        if self.drop_rect.intersects(self.geometry()):
            self.hide()
            self.on_dropped()
        else:
            self.reset_position()


class MiniGamePanelWindow(QWidget):
    def __init__(self, base_dir: Path, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.base_dir = base_dir
        self.state = build_default_game()
        self.choice_buttons: List[PixelButton] = []
        self.clue_cards: List[QLabel] = []
        self.reward_rows: List[QLabel] = []
        self.setWindowTitle("MoodPet 小游戏")
        self.setFixedSize(1360, 760)
        self.setStyleSheet(f"background-color: {CREAM};")
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        self._build_chrome()
        self._build_sidebar()
        self._build_story_area()
        self._build_right_panel()

    def _build_chrome(self) -> None:
        top = QFrame(self)
        top.setGeometry(4, 4, 1352, 54)
        top.setStyleSheet(f"background-color: #55d0bd; border: 3px solid {NAVY}; border-radius: 4px;")
        label(top, "✿ MoodPet 陪伴中", (20, 6, 280, 38), 17, 900).setStyleSheet("color: white; border: none; background: transparent;")
        self.min_button = PixelButton("—", top, "#fffaf2")
        self.min_button.setGeometry(1248, 10, 34, 32)
        self.min_button.clicked.connect(self.showMinimized)
        self.close_button = PixelButton("", top, PINK, "white")
        self.close_button.setGeometry(1296, 10, 34, 32)
        apply_button_icon(self.close_button, "close", 24)
        self.close_button.clicked.connect(self.hide)

        crumb = QFrame(self)
        crumb.setGeometry(272, 64, 1078, 44)
        crumb.setStyleSheet(f"background-color: #fffaf2; border: 2px solid {SOFT_LINE}; border-radius: 3px;")
        label(crumb, "⌂  >  功能导航  >  小游戏", (24, 4, 360, 34), 15, 900)

    def _build_sidebar(self) -> None:
        side = QFrame(self)
        side.setGeometry(10, 64, 250, 686)
        side.setStyleSheet(f"background-color: #fff4df; border: 3px solid {NAVY}; border-radius: 7px;")

        pet = QLabel(side)
        pet.setGeometry(68, 22, 116, 116)
        movie = QMovie(str(self.base_dir / "pet" / "init" / "stay.gif"))
        movie.setScaledSize(QSize(112, 112))
        pet.setMovie(movie)
        movie.start()
        self.sidebar_pet_movie = movie

        items = [
            ("≋", "实时检测", "#b9ed9e"),
            ("☑", "待办", "#fff7e9"),
            ("☄", "小游戏  ›", LILAC),
            ("⚙", "设置", "#fff7e9"),
        ]
        for index, (icon, title, color) in enumerate(items):
            item = QLabel(f"{icon}   {title}", side)
            item.setGeometry(24, 166 + index * 94, 202, 72)
            border = NAVY if "小游戏" in title else LINE
            item.setStyleSheet(
                f"background-color: {color}; color: {INK}; border: 2px solid {border}; border-radius: 6px;"
                "font: 900 14pt 'Microsoft YaHei'; padding-left: 16px;"
            )

        footer = QFrame(side)
        footer.setGeometry(0, 636, 250, 50)
        footer.setStyleSheet(f"background-color: {NAVY}; border: none; border-radius: 0;")
        label(footer, "♥  MoodPet 陪伴中", (20, 9, 170, 30), 11, 900).setStyleSheet(
            "color: #ffd77d; border: none; font: 900 11pt 'Microsoft YaHei';"
        )
        label(footer, "▂▃▆", (196, 9, 44, 30), 13, 900).setStyleSheet(
            "color: #91f18b; border: none; font: 900 13pt 'Microsoft YaHei';"
        )

    def _build_story_area(self) -> None:
        self.header_card = QFrame(self)
        self.header_card.setGeometry(282, 118, 740, 146)
        self.header_card.setStyleSheet(f"background-color: {PANEL}; border: 2px solid {SOFT_LINE}; border-radius: 8px;")
        self.thumb = QLabel("", self.header_card)
        self.thumb.setGeometry(22, 22, 88, 88)
        self.thumb.setAlignment(Qt.AlignCenter)
        apply_label_icon(self.thumb, "story_clue", 48)
        self.thumb.setStyleSheet(
            "background-color: #2e4666; color: #ffd28d; border: 3px solid #102943;"
            "border-radius: 5px; font: 900 24pt 'Microsoft YaHei';"
        )
        self.story_title = label(self.header_card, "", (138, 18, 360, 32), 17, 900)
        self.subtitle = label(self.header_card, "", (140, 52, 390, 28), 11, 700)
        self.progress_label = label(self.header_card, "", (140, 84, 100, 26), 11, 800)
        self.progress_nodes = label(self.header_card, "① 开场 ━ ② 事件 ━ ③ 选择 ━ ④ 线索 ━ ⑤ 结尾", (250, 82, 430, 28), 10, 900)
        self.continue_button = PixelButton("继续故事", self.header_card, BLUE, "white")
        self.continue_button.setGeometry(552, 30, 140, 48)
        apply_button_icon(self.continue_button, "story_choice", 24)
        self.continue_button.clicked.connect(self._continue_story)

        self.scene = PostalScene(self)
        self.scene.setGeometry(282, 276, 374, 306)

        self.event_panel = QFrame(self)
        self.event_panel.setGeometry(668, 276, 354, 236)
        self.event_panel.setStyleSheet(f"background-color: {PANEL}; border: 2px solid {SOFT_LINE}; border-radius: 8px;")
        self.node_title = label(self.event_panel, "", (22, 12, 250, 28), 12, 900)
        self.node_prompt = label(self.event_panel, "", (22, 42, 310, 48), 11, 900)
        for index in range(3):
            button = PixelButton("", self.event_panel, "#fffaf2")
            button.setGeometry(28, 96 + index * 44, 298, 36)
            self.choice_buttons.append(button)

        self.clue_panel = QFrame(self)
        self.clue_panel.setGeometry(282, 596, 300, 126)
        self.clue_panel.setStyleSheet(f"background-color: {PANEL}; border: 2px solid {SOFT_LINE}; border-radius: 8px;")
        self.clue_title = label(self.clue_panel, "", (18, 8, 180, 28), 12, 900)
        for index in range(3):
            clue = QLabel(self.clue_panel)
            clue.setGeometry(18 + index * 92, 44, 82, 66)
            clue.setAlignment(Qt.AlignCenter)
            clue.setWordWrap(True)
            self.clue_cards.append(clue)

        self.interaction_panel = QFrame(self)
        self.interaction_panel.setGeometry(594, 596, 296, 126)
        self.interaction_panel.setStyleSheet(f"background-color: {PANEL}; border: 2px solid {SOFT_LINE}; border-radius: 8px;")
        label(self.interaction_panel, "☝ 轻量互动", (18, 8, 150, 26), 12, 900)
        label(self.interaction_panel, "整理散落信笺（拖拽归位）", (18, 32, 200, 24), 10, 700)
        self.drop_target = QLabel("信封", self.interaction_panel)
        self.drop_target.setGeometry(196, 54, 76, 46)
        self.drop_target.setAlignment(Qt.AlignCenter)
        self.drop_target.setStyleSheet(
            "background-color: #fffaf2; color: #9a7256; border: 2px dashed #b99169;"
            "border-radius: 5px; font: 900 11pt 'Microsoft YaHei';"
        )
        self.envelope = DraggableEnvelope(self.interaction_panel, self.drop_target.geometry(), self._complete_interaction)
        self.interaction_tip = label(self.interaction_panel, "提示：将信纸拖到信封里", (104, 96, 172, 22), 8, 700)

        self.pet_note = QLabel(self)
        self.pet_note.setGeometry(900, 586, 112, 74)
        self.pet_note.setWordWrap(True)
        self.pet_note.setStyleSheet(
            f"background-color: {PANEL}; color: {INK}; border: 2px solid {LINE};"
            "font-family: 'Microsoft YaHei'; font-size: 10pt; font-weight: 900; padding: 8px;"
        )
        pet = QLabel(self)
        pet.setGeometry(930, 658, 92, 72)
        note_movie = QMovie(str(self.base_dir / "pet" / "init" / "stay.gif"))
        note_movie.setScaledSize(QSize(82, 82))
        pet.setMovie(note_movie)
        note_movie.start()
        self.note_pet_movie = note_movie

    def _build_right_panel(self) -> None:
        self.theme_card = self._right_card(1040, 118, 292, 132, "当前故事主题")
        self.theme_subject = label(self.theme_card, "", (24, 38, 240, 24), 11, 800)
        self.theme_mood = label(self.theme_card, "", (24, 66, 240, 24), 11, 800)
        self.theme_style = label(self.theme_card, "", (24, 94, 240, 24), 11, 800)

        self.feedback_card = self._right_card(1040, 266, 292, 116, "桌宠反馈")
        mascot = QLabel(self.feedback_card)
        mascot.setGeometry(18, 38, 72, 66)
        movie = QMovie(str(self.base_dir / "pet" / "init" / "stay.gif"))
        movie.setScaledSize(QSize(70, 70))
        mascot.setMovie(movie)
        movie.start()
        self.feedback_pet_movie = movie
        self.feedback = label(self.feedback_card, "", (104, 42, 162, 48), 12, 900)

        links = self._right_card(1040, 398, 292, 116, "现实功能连接")
        self.todo_button = PixelButton("☷ 去待办", links, "#ffd9df")
        self.todo_button.setGeometry(20, 46, 78, 42)
        self.break_button = PixelButton("☕ 休息", links, "#ffe2a8")
        self.break_button.setGeometry(108, 46, 78, 42)
        self.focus_button = PixelButton("◎ 专注", links, "#bfe1ff")
        self.focus_button.setGeometry(196, 46, 84, 42)
        self.todo_button.clicked.connect(lambda: self._set_feedback("待办入口已准备好，稍后可以接入真实任务。"))
        self.break_button.clicked.connect(lambda: self._set_feedback("先喝口水，故事会在这里等你。"))
        self.focus_button.clicked.connect(lambda: self._set_feedback("专注模式模拟启动：25 分钟小邮差计时。"))

        rewards = self._right_card(1040, 530, 292, 132, "本次故事收获")
        for index in range(4):
            row = label(rewards, "", (24, 38 + index * 24, 230, 22), 10, 800)
            self.reward_rows.append(row)

        self.restart_button = PixelButton("重新开始", self, MINT, "white")
        self.restart_button.setGeometry(1048, 672, 274, 42)
        apply_button_icon(self.restart_button, "restart", 24)
        self.restart_button.clicked.connect(self._restart)
        self.back_button = PixelButton("返回导航", self, BLUE, "white")
        self.back_button.setGeometry(1048, 716, 274, 32)
        apply_button_icon(self.back_button, "back", 24)
        self.back_button.clicked.connect(self.hide)

    def _right_card(self, x: int, y: int, w: int, h: int, title: str) -> QFrame:
        card = QFrame(self)
        card.setGeometry(x, y, w, h)
        card.setStyleSheet(f"background-color: {PANEL}; border: 2px solid {SOFT_LINE}; border-radius: 8px;")
        label(card, title, (20, 8, w - 40, 26), 12, 900)
        return card

    def refresh(self) -> None:
        node = current_node(self.state)
        self.story_title.setText(f"本次故事： {self.state.story_title}")
        self.subtitle.setText(self.state.subtitle)
        self.progress_label.setText(progress_text(self.state))
        self.scene.set_caption(node.scene_text)
        self.node_title.setText(node.title)
        self.node_prompt.setText(node.prompt)
        self.pet_note.setText(node.pet_reply)
        self.feedback.setText(node.pet_reply)

        choices = available_choices(self.state)
        for index, button in enumerate(self.choice_buttons):
            if index < len(choices):
                choice = choices[index]
                button.setText(choice.title)
                apply_button_icon(button, "story_choice", 24)
                button.show()
                try:
                    button.clicked.disconnect()
                except TypeError:
                    pass
                button.clicked.connect(lambda checked=False, choice_id=choice.id: self._choose(choice_id))
            else:
                button.hide()

        self.clue_title.setText(f"🔎 已收集线索        {collected_count_text(self.state)}")
        collected = [clue for clue in self.state.clues if clue.collected]
        for index, card in enumerate(self.clue_cards):
            if index < len(collected[-3:]):
                clue = collected[-3:][index]
                card.setText(f"{clue.icon}\n{clue.title}")
                card.setStyleSheet(
                    "background-color: #fffaf2; color: #10151b; border: 2px solid #b99169;"
                    "border-radius: 5px; font: 900 10pt 'Microsoft YaHei';"
                )
            else:
                card.setText("？")
                card.setStyleSheet(
                    "background-color: #f5e8d7; color: #9a7256; border: 2px dashed #c7a989;"
                    "border-radius: 5px; font: 900 14pt 'Microsoft YaHei';"
                )

        self.theme_subject.setText(f"✉ 主题：   {self.state.theme_subject}")
        self.theme_mood.setText(f"♧ 氛围：   {self.state.theme_mood}")
        self.theme_style.setText(f"★ 风格：   {self.state.theme_style}")

        for index, reward in enumerate(self.state.rewards):
            self.reward_rows[index].setText(f"{reward.icon}  {reward.label:<8} +{reward.value}")
        self.reward_rows[3].setText(f"▤  线索记录       {collected_count_text(self.state)}")

        self.envelope.setVisible(not self.state.interaction_done)
        if not self.state.interaction_done:
            self.envelope.reset_position()
            self.interaction_tip.setText("提示：将信纸拖到信封里")
        else:
            self.interaction_tip.setText("已归位：信纸安静地躺在信封里")

    def _choose(self, choice_id: str) -> None:
        self.state = choose_event(self.state, choice_id)
        self.refresh()

    def _complete_interaction(self) -> None:
        self.state = complete_interaction(self.state)
        self.refresh()

    def _continue_story(self) -> None:
        if self.state.interaction_done and self.state.node_index < 4:
            self.state = MiniGameState(
                story_title=self.state.story_title,
                subtitle=self.state.subtitle,
                theme_subject=self.state.theme_subject,
                theme_mood=self.state.theme_mood,
                theme_style=self.state.theme_style,
                node_index=4,
                nodes=self.state.nodes,
                choices=self.state.choices,
                clues=self.state.clues,
                rewards=self.state.rewards,
                interaction_done=True,
            )
        elif not self.state.interaction_done:
            self._set_feedback("先完成轻量互动，把信纸拖回信封里。")
        self.refresh()

    def _restart(self) -> None:
        self.state = restart_game(self.state)
        self.refresh()

    def _set_feedback(self, text: str) -> None:
        self.feedback.setText(text)
