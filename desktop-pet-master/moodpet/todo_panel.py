from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QMovie
from PyQt5.QtWidgets import QFrame, QLabel, QLineEdit, QPushButton, QWidget

from moodpet.pixel_icons import apply_button_icon, apply_label_icon
from moodpet.todo_state import (
    CATEGORY_COLORS,
    DEFAULT_TODOS,
    TodoItem,
    add_todo,
    assistant_message,
    completion_ratio,
    completion_text,
    fatigue_level,
    today_label,
    toggle_completed,
    toggle_starred,
    visible_todos,
)


INK = "#10151b"
NAVY = "#062b36"
TEAL = "#18c7a4"
CREAM = "#fff1da"
PANEL = "#fff7e9"
LINE = "#d5b58c"
PINK = "#ff6374"
MINT = "#19b995"
BLUE = "#6fb3ff"
GOLD = "#ffc843"


def make_label(parent: QWidget, text: str, x: int, y: int, w: int, h: int, size: int = 13, weight: int = 700) -> QLabel:
    widget = QLabel(text, parent)
    widget.setGeometry(x, y, w, h)
    widget.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    widget.setStyleSheet(
        f"color: {INK}; border: none; font-family: 'Microsoft YaHei'; font-size: {size}pt; font-weight: {weight};"
    )
    return widget


class PixelButton(QPushButton):
    def __init__(self, text: str, parent: QWidget, color: str = PANEL, text_color: str = INK) -> None:
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(
            "QPushButton {"
            f"background-color: {color};"
            f"color: {text_color};"
            "border: 2px solid #b99169;"
            "border-right: 4px solid #7d6046;"
            "border-bottom: 4px solid #7d6046;"
            "border-radius: 5px;"
            "font-family: 'Microsoft YaHei';"
            "font-size: 12pt;"
            "font-weight: 900;"
            "padding: 7px 12px;"
            "}"
            "QPushButton:hover { background-color: #fffaf2; }"
            "QPushButton:pressed { padding-left: 14px; padding-top: 9px; }"
        )


def pixel_shadow(parent: QWidget, x: int, y: int, w: int, h: int, radius: int = 8, color: str = "#c49b73") -> QFrame:
    shadow = QFrame(parent)
    shadow.setGeometry(x + 5, y + 5, w, h)
    shadow.setStyleSheet(f"background-color: {color}; border: none; border-radius: {radius}px;")
    shadow.lower()
    return shadow


class TodoPanelWindow(QWidget):
    def __init__(self, base_dir: Path, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.base_dir = base_dir
        self.todos: List[TodoItem] = list(DEFAULT_TODOS)
        self.active_tab = "today"
        self.sort_mode = "time"
        self.row_frames: List[QFrame] = []
        self.setWindowTitle("MoodPet 待办")
        self.setFixedSize(1360, 760)
        self.setStyleSheet(f"background-color: {CREAM};")
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        self._build_chrome()
        self._build_left_panel()
        self._build_assistant_panel()

    def _build_chrome(self) -> None:
        top = QFrame(self)
        top.setGeometry(4, 4, 1352, 52)
        top.setStyleSheet(
            f"background-color: #51d1bd; border: 3px solid {NAVY}; border-bottom-width: 4px; border-radius: 4px;"
        )
        make_label(top, "🐾 MoodPet", 18, 6, 320, 38, 18, 900).setStyleSheet(
            "color: white; border: none; font-family: 'Microsoft YaHei'; font-size: 18pt; font-weight: 900;"
        )

        self.min_button = PixelButton("—", top, "#fffaf2")
        self.min_button.setGeometry(1228, 9, 34, 30)
        self.min_button.clicked.connect(self.showMinimized)
        self.close_button = PixelButton("", top, PINK, "white")
        self.close_button.setGeometry(1278, 9, 34, 30)
        apply_button_icon(self.close_button, "close", 24)
        self.close_button.clicked.connect(self.hide)

        crumb = QFrame(self)
        crumb.setGeometry(8, 60, 1344, 46)
        crumb.setStyleSheet(f"background-color: #fffaf2; border: 2px solid {LINE}; border-radius: 3px;")
        make_label(crumb, "⌂  功能导航   ›   待办", 26, 5, 320, 34, 15, 900)

        footer = QFrame(self)
        footer.setGeometry(4, 710, 1352, 44)
        footer.setStyleSheet(f"background-color: {NAVY}; border: 3px solid #071927; border-radius: 4px;")
        make_label(footer, "🐱  专注每一步，进步看得见 ✨", 96, 5, 360, 32, 12, 900).setStyleSheet(
            "color: #fff5cc; border: none; font-family: 'Microsoft YaHei'; font-size: 12pt; font-weight: 900;"
        )
        make_label(footer, "♥  MoodPet 陪伴中", 1078, 5, 230, 32, 12, 900).setStyleSheet(
            "color: #fff5cc; border: none; font-family: 'Microsoft YaHei'; font-size: 12pt; font-weight: 900;"
        )
        make_label(footer, "▂▅▇", 1306, 5, 44, 32, 15, 900).setStyleSheet(
            "color: #91f18b; border: none; font-family: 'Microsoft YaHei'; font-size: 15pt; font-weight: 900;"
        )

    def _build_left_panel(self) -> None:
        self.left_shadow = pixel_shadow(self, 34, 120, 880, 568, 8, "#d8b98f")
        self.left_panel = QFrame(self)
        self.left_panel.setGeometry(34, 120, 880, 568)
        self.left_panel.setStyleSheet(
            f"background-color: {PANEL}; border: 2px solid {LINE};"
            "border-right: 4px solid #c99462; border-bottom: 4px solid #c99462; border-radius: 8px;"
        )

        icon = QLabel("", self.left_panel)
        icon.setGeometry(28, 24, 70, 70)
        icon.setAlignment(Qt.AlignCenter)
        apply_label_icon(icon, "todo", 40)
        icon.setStyleSheet(
            "background-color: #fff0f3; border: 3px solid #f29aaa; border-radius: 10px;"
            "font-family: 'Microsoft YaHei'; font-size: 26pt;"
        )
        make_label(self.left_panel, "待办", 118, 20, 170, 42, 20, 900)
        make_label(self.left_panel, "管理你的任务，保持专注与好心情", 118, 60, 430, 32, 13, 700)

        self.progress_panel = QFrame(self.left_panel)
        self.progress_panel.setGeometry(652, 32, 210, 62)
        self.progress_panel.setStyleSheet(
            "background-color: #fffaf2; border: 1px solid #e1bd91;"
            "border-right: 3px solid #d29c67; border-bottom: 3px solid #d29c67; border-radius: 7px;"
        )
        self.progress_text = make_label(self.progress_panel, "", 18, 8, 160, 28, 14, 900)
        self.progress_track = QFrame(self.progress_panel)
        self.progress_track.setGeometry(18, 42, 172, 12)
        self.progress_track.setStyleSheet("background-color: #ffe2b8; border: 1px solid #c68d4f; border-radius: 5px;")
        self.progress_fill = QFrame(self.progress_track)
        self.progress_fill.setGeometry(0, 0, 60, 12)
        self.progress_fill.setStyleSheet(f"background-color: {MINT}; border: none; border-radius: 5px;")

        self.today_tab = PixelButton("▣  今日任务（4）", self.left_panel, "#fffaf2")
        self.today_tab.setGeometry(18, 118, 238, 52)
        self.today_tab.clicked.connect(lambda: self._set_tab("today"))
        self.done_tab = PixelButton("☑  已完成（1）", self.left_panel, "#fffaf2")
        self.done_tab.setGeometry(266, 124, 190, 46)
        self.done_tab.clicked.connect(lambda: self._set_tab("completed"))
        self.filter_button = PixelButton("▽  筛选", self.left_panel, "#fffaf2")
        self.filter_button.setGeometry(628, 124, 112, 40)
        self.filter_button.clicked.connect(self._cycle_filter)
        self.sort_button = PixelButton("↕  排序", self.left_panel, "#fffaf2")
        self.sort_button.setGeometry(756, 124, 104, 40)
        self.sort_button.clicked.connect(self._cycle_sort)

        self.date_label = make_label(self.left_panel, "", 36, 184, 360, 32, 12, 800)

        self.list_panel = QFrame(self.left_panel)
        self.list_panel.setGeometry(28, 222, 820, 250)
        self.list_panel.setStyleSheet("background: transparent; border: none;")

        self.input = QLineEdit(self.left_panel)
        self.input.setGeometry(40, 490, 636, 72)
        self.input.setPlaceholderText("＋  添加新任务...")
        self.input.setStyleSheet(
            "QLineEdit { background-color: #fffaf2; border: 2px dashed #bda890; border-radius: 7px;"
            "font-family: 'Microsoft YaHei'; font-size: 14pt; font-weight: 900; color: #10151b; padding-left: 18px; }"
        )
        self.input.returnPressed.connect(self._add_task)
        self.add_button = PixelButton("添加任务", self.left_panel, MINT, "white")
        self.add_button.setGeometry(696, 502, 140, 52)
        self.add_button.clicked.connect(self._add_task)

    def _build_assistant_panel(self) -> None:
        self.right_shadow = pixel_shadow(self, 934, 120, 392, 568, 10, "#8eb9e8")
        self.right_panel = QFrame(self)
        self.right_panel.setGeometry(934, 120, 392, 568)
        self.right_panel.setStyleSheet(
            "background-color: #d8ebff; border: 3px solid #4a8ad9;"
            "border-right: 5px solid #2c70bf; border-bottom: 5px solid #2c70bf; border-radius: 10px;"
        )
        make_label(self.right_panel, "🐾  MoodPet 小助手  🐾", 70, 8, 280, 34, 13, 900)

        mood_card = QFrame(self.right_panel)
        mood_card.setGeometry(20, 52, 350, 128)
        mood_card.setStyleSheet(
            f"background-color: {PANEL}; border: 2px solid {LINE};"
            "border-right: 3px solid #c99462; border-bottom: 3px solid #c99462; border-radius: 8px;"
        )
        make_label(mood_card, "今日心情： 有点疲惫 😔", 22, 14, 310, 32, 14, 900)
        make_label(mood_card, "🐱", 28, 54, 54, 48, 25, 900)
        self.energy_track = QFrame(mood_card)
        self.energy_track.setGeometry(88, 70, 226, 16)
        self.energy_track.setStyleSheet("background-color: #ffe2b8; border: 1px solid #a16f3f; border-radius: 6px;")
        self.energy_fill = QFrame(self.energy_track)
        self.energy_fill.setGeometry(0, 0, 150, 16)
        self.energy_fill.setStyleSheet("background-color: #ffd34f; border-right: 4px solid #18b888; border-radius: 5px;")
        self.fatigue_label = make_label(mood_card, "", 88, 90, 180, 28, 11, 800)

        self.bubble = QLabel("", self.right_panel)
        self.bubble.setGeometry(26, 190, 286, 116)
        self.bubble.setWordWrap(True)
        self.bubble.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.bubble.setStyleSheet(
            "background-color: #fffaf2; color: #10151b; border: 3px solid #a84545; border-radius: 4px;"
            "font-family: 'Microsoft YaHei'; font-size: 12pt; font-weight: 900; padding: 12px;"
        )

        mascot = QLabel(self.right_panel)
        mascot.setGeometry(178, 314, 136, 136)
        movie = QMovie(str(self.base_dir / "pet" / "init" / "stay.gif"))
        movie.setScaledSize(QSize(148, 148))
        mascot.setMovie(movie)
        movie.start()
        self.mascot_movie = movie

        recommend = QFrame(self.right_panel)
        recommend.setGeometry(14, 466, 362, 86)
        recommend.setStyleSheet(
            f"background-color: {PANEL}; border: 2px solid {LINE};"
            "border-right: 3px solid #c99462; border-bottom: 3px solid #c99462; border-radius: 7px;"
        )
        make_label(recommend, "⭐  为你推荐", 18, 2, 160, 30, 12, 900)
        make_label(recommend, "●", 20, 36, 36, 34, 20, 900).setStyleSheet(
            "color: #f44336; border: none; font-family: 'Microsoft YaHei'; font-size: 20pt; font-weight: 900;"
        )
        make_label(recommend, "番茄钟专注 25 分钟", 60, 28, 176, 24, 10, 900)
        make_label(recommend, "专注一段，效率更高", 60, 51, 166, 20, 8, 700)
        self.focus_button = PixelButton("开始专注", recommend, MINT, "white")
        self.focus_button.setGeometry(244, 36, 108, 38)
        self.focus_button.clicked.connect(self._focus_done)

    def _create_row(self, item: TodoItem, y: int) -> QFrame:
        row = QFrame(self.list_panel)
        row.setGeometry(0, y, 820, 56)
        bg = "#edf8e6" if item.completed else "#fffaf2"
        row.setStyleSheet(f"background-color: {bg}; border: 1px solid #e1bd91; border-radius: 7px;")

        check = QPushButton("✓" if item.completed else "", row)
        check.setGeometry(20, 14, 30, 30)
        check.setCursor(Qt.PointingHandCursor)
        check.setStyleSheet(
            "QPushButton { background-color: "
            + (MINT if item.completed else "#fffaf2")
            + "; color: white; border: 2px solid #d9a26f; border-radius: 4px;"
            "font-family: 'Microsoft YaHei'; font-size: 17pt; font-weight: 900; }"
        )
        check.clicked.connect(lambda checked=False, item_id=item.id: self._toggle_completed(item_id))

        title = make_label(row, item.title, 70, 12, 252, 32, 12, 900)
        if item.completed:
            title.setStyleSheet(
                "color: #222; border: none; font-family: 'Microsoft YaHei'; font-size: 12pt; font-weight: 900;"
            )

        chip_color = CATEGORY_COLORS.get(item.category, BLUE)
        chip = QLabel(item.category, row)
        chip.setGeometry(330, 16, 54, 26)
        chip.setAlignment(Qt.AlignCenter)
        chip.setStyleSheet(
            f"background-color: #fff7e9; color: {chip_color}; border: 1px solid {chip_color};"
            "border-radius: 4px; font-family: 'Microsoft YaHei'; font-size: 10pt; font-weight: 900;"
        )

        status = item.completed_at + " 完成" if item.completed else f"◷  {item.due_time} 截止"
        make_label(row, status, 610, 12, 130, 32, 11, 700)

        star = QPushButton("★" if item.starred else "☆", row)
        star.setGeometry(758, 12, 34, 34)
        star.setCursor(Qt.PointingHandCursor)
        star.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {GOLD if item.starred else '#d0935f'};"
            "border: none; font-family: 'Microsoft YaHei'; font-size: 21pt; font-weight: 900; }}"
        )
        star.clicked.connect(lambda checked=False, item_id=item.id: self._toggle_starred(item_id))
        return row

    def _set_tab(self, tab: str) -> None:
        self.active_tab = tab
        self.refresh()

    def _cycle_filter(self) -> None:
        modes = ["time", "category", "starred"]
        self.sort_mode = modes[(modes.index(self.sort_mode) + 1) % len(modes)]
        self.refresh()

    def _cycle_sort(self) -> None:
        self.todos = list(reversed(visible_todos(self.todos, "today", self.sort_mode)))
        self.refresh()

    def _add_task(self) -> None:
        self.todos = add_todo(self.todos, self.input.text(), "生活", "今天")
        self.input.clear()
        self.active_tab = "today"
        self.refresh()

    def _toggle_completed(self, item_id: int) -> None:
        self.todos = toggle_completed(self.todos, item_id, datetime.now().strftime("%H:%M"))
        self.refresh()

    def _toggle_starred(self, item_id: int) -> None:
        self.todos = toggle_starred(self.todos, item_id)
        self.refresh()

    def _focus_done(self) -> None:
        self.input.setText("番茄钟专注 25 分钟")
        self._add_task()

    def refresh(self) -> None:
        for frame in self.row_frames:
            frame.setParent(None)
            frame.deleteLater()
        self.row_frames = []

        done_count = sum(1 for item in self.todos if item.completed)
        total_count = len(self.todos)
        done_visible = sum(1 for item in self.todos if item.completed)
        self.today_tab.setText(f"▣  今日任务（{total_count}）")
        self.done_tab.setText(f"☑  已完成（{done_visible}）")
        self.progress_text.setText(completion_text(self.todos))
        self.progress_fill.setFixedWidth(max(0, min(172, int(172 * completion_ratio(self.todos)))))
        self.date_label.setText("▦  " + today_label())
        self.filter_button.setText({"time": "▽  筛选", "category": "▤  分类", "starred": "★  星标"}[self.sort_mode])

        self.today_tab.setStyleSheet(self._tab_style(self.active_tab == "today"))
        self.done_tab.setStyleSheet(self._tab_style(self.active_tab == "completed"))

        rows = visible_todos(self.todos, self.active_tab, self.sort_mode)
        for index, item in enumerate(rows[:4]):
            row = self._create_row(item, index * 60)
            row.show()
            self.row_frames.append(row)

        fatigue = fatigue_level(done_count, total_count)
        self.energy_fill.setFixedWidth(max(0, min(226, int(226 * fatigue / 100))))
        self.fatigue_label.setText(f"疲惫度： {fatigue}%")
        self.bubble.setText(assistant_message(self.todos) + " ✨")

    def _tab_style(self, selected: bool) -> str:
        border = "#2379d4" if selected else "#b99169"
        bg = "#fffaf2" if selected else "#fff7e9"
        return (
            "QPushButton {"
            f"background-color: {bg}; color: #102943; border: 2px solid {border}; border-radius: 8px;"
            "font-family: 'Microsoft YaHei'; font-size: 13pt; font-weight: 900; padding: 8px 12px;"
            "}"
            "QPushButton:hover { background-color: #fffaf2; }"
        )
