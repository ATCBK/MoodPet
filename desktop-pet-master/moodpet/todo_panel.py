from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional

from PyQt5.QtCore import QPoint, QSize, Qt, QTimer
from PyQt5.QtGui import QIcon, QMovie
from PyQt5.QtWidgets import QFrame, QLabel, QLineEdit, QPushButton, QScrollArea, QWidget

from moodpet.pixel_icons import apply_button_icon, apply_label_icon
from moodpet.side_nav import build_pet_sidebar
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
            "background-image: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(255,255,255,0.55), stop:0.55 rgba(255,255,255,0.08), stop:1 rgba(0,0,0,0.03));"
            f"color: {text_color};"
            "border: 2px solid #b99169;"
            "border-right: 4px solid #7d6046;"
            "border-bottom: 4px solid #7d6046;"
            "border-radius: 7px;"
            "font-family: 'Microsoft YaHei';"
            "font-size: 11pt;"
            "font-weight: 900;"
            "padding: 6px 11px;"
            "min-height: 34px;"
            "}"
            "QPushButton:hover { background-color: #fffaf2; }"
            "QPushButton:pressed { padding-left: 10px; padding-top: 8px; }"
        )


def pixel_shadow(parent: QWidget, x: int, y: int, w: int, h: int, radius: int = 8, color: str = "#c49b73") -> QFrame:
    shadow = QFrame(parent)
    shadow.setGeometry(x + 7, y + 7, w, h)
    shadow.setStyleSheet(f"background-color: {color}; border: none; border-radius: {radius}px;")
    shadow.lower()
    return shadow


class TodoPanelWindow(QWidget):
    def __init__(
        self,
        base_dir: Path,
        parent: Optional[QWidget] = None,
        open_target: Optional[Callable[[str], None]] = None,
    ) -> None:
        super().__init__(parent)
        self.base_dir = base_dir
        self.open_target = open_target or (lambda module_id: None)
        self._chrome_dragging = False
        self._chrome_drag_pos = QPoint()
        self.todos: List[TodoItem] = list(DEFAULT_TODOS)
        self.active_tab = "today"
        self.sort_mode = "time"
        self.row_frames: List[QFrame] = []
        self.focus_remaining_seconds = 0
        self.focus_timer = QTimer(self)
        self.focus_timer.timeout.connect(self._tick_focus_timer)
        self.setWindowTitle("MoodPet 待办")
        self.setFixedSize(1630, 760)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setStyleSheet(f"background-color: {CREAM};")
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        self._build_chrome()
        self._build_left_panel()
        self._build_assistant_panel()
        self._shift_content_for_sidebar()
        self.sidebar, self.sidebar_items = build_pet_sidebar(self, "todo", self.open_target)

    def _shift_content_for_sidebar(self) -> None:
        for child in self.findChildren(QWidget, options=Qt.FindDirectChildrenOnly):
            child.move(child.x() + 270, child.y())

    def _build_chrome(self) -> None:
        top = QFrame(self)
        self.top = top
        top.setCursor(Qt.OpenHandCursor)
        top.mousePressEvent = self._chrome_mouse_press
        top.mouseMoveEvent = self._chrome_mouse_move
        top.mouseReleaseEvent = self._chrome_mouse_release
        top.setGeometry(4, 4, 1352, 52)
        top.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #7be7d7, stop:0.48 #47ceb7, stop:1 #2fae9c);"
            f"border: 3px solid {NAVY}; border-bottom-width: 4px; border-radius: 5px;"
        )
        icon_shell = QFrame(top)
        icon_shell.setGeometry(14, 10, 30, 30)
        icon_shell.setStyleSheet(
            "QFrame {"
            "background: rgba(255, 255, 255, 0.82);"
            f"border: 2px solid {NAVY};"
            f"border-right: 4px solid {NAVY};"
            f"border-bottom: 4px solid {NAVY};"
            "border-radius: 7px;"
            "}"
        )
        icon = QLabel(icon_shell)
        icon.setGeometry(4, 4, 22, 22)
        icon.setAlignment(Qt.AlignCenter)
        icon.setPixmap(QIcon(str(self.base_dir / "mypetico.ico")).pixmap(22, 22))
        make_label(top, "MoodPet 待办", 46, 6, 290, 38, 18, 900).setStyleSheet(
            "color: white; border: none; font-family: 'Microsoft YaHei'; font-size: 18pt; font-weight: 900;"
        )

        self.min_button = PixelButton("—", top, "#fffaf2")
        self.min_button.setGeometry(1228, 9, 34, 30)
        self.min_button.clicked.connect(self.showMinimized)
        self.max_button = QPushButton("□", top)
        self.max_button.setGeometry(1278, 9, 34, 30)
        self.max_button.setCursor(Qt.PointingHandCursor)
        self.max_button.setStyleSheet(
            "QPushButton {"
            "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ecfffb, stop:1 #c9f2eb);"
            f"color: {NAVY};"
            f"border: 2px solid {NAVY};"
            f"border-right: 4px solid {NAVY};"
            f"border-bottom: 4px solid {NAVY};"
            "border-radius: 5px;"
            "font-family: 'Microsoft YaHei';"
            "font-size: 12pt;"
            "font-weight: 900;"
            "padding: 0;"
            "}"
            "QPushButton:hover { background: #f7fffd; }"
            "QPushButton:pressed { padding-left: 1px; padding-top: 2px; }"
        )
        self.max_button.clicked.connect(self._toggle_window_state)
        self.close_button = PixelButton("", top, PINK, "white")
        self.close_button.setGeometry(1318, 9, 30, 30)
        apply_button_icon(self.close_button, "close", 24)
        self.close_button.clicked.connect(self.hide)

        crumb = QFrame(self)
        crumb.setGeometry(8, 60, 1344, 46)
        crumb.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #fffef8, stop:1 #f7ecda);"
            f"border: 2px solid {LINE}; border-right: 4px solid #c9a06f; border-bottom: 4px solid #c9a06f; border-radius: 4px;"
        )
        make_label(crumb, "⌂  功能导航   ›   待办", 26, 5, 320, 34, 15, 900)

        footer = QFrame(self)
        footer.setGeometry(4, 710, 1352, 44)
        footer.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0d3c4c, stop:1 #061f29);"
            "border: 3px solid #071927; border-right: 5px solid #04141d; border-bottom: 5px solid #04141d; border-radius: 4px;"
        )
        make_label(footer, "🐱  专注每一步，进步看得见 ✨", 96, 5, 360, 32, 12, 900).setStyleSheet(
            "color: #fff5cc; border: none; font-family: 'Microsoft YaHei'; font-size: 12pt; font-weight: 900;"
        )
        make_label(footer, "♥  MoodPet 陪伴中", 1078, 5, 230, 32, 12, 900).setStyleSheet(
            "color: #fff5cc; border: none; font-family: 'Microsoft YaHei'; font-size: 12pt; font-weight: 900;"
        )
        make_label(footer, "▂▅▇", 1306, 5, 44, 32, 15, 900).setStyleSheet(
            "color: #91f18b; border: none; font-family: 'Microsoft YaHei'; font-size: 15pt; font-weight: 900;"
        )

    def _chrome_mouse_press(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._chrome_dragging = True
            self._chrome_drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            self.top.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return
        event.ignore()

    def _chrome_mouse_move(self, event) -> None:
        if self._chrome_dragging and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self._chrome_drag_pos)
            event.accept()
            return
        event.ignore()

    def _chrome_mouse_release(self, event) -> None:
        self._chrome_dragging = False
        self.top.setCursor(Qt.OpenHandCursor)
        event.accept()

    def _toggle_window_state(self) -> None:
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def _build_left_panel(self) -> None:
        self.left_shadow = pixel_shadow(self, 34, 120, 880, 568, 10, "#b98e61")
        self.left_panel = QFrame(self)
        self.left_panel.setGeometry(34, 120, 880, 568)
        self.left_panel.setStyleSheet(
            f"background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #fffdf7, stop:1 {PANEL});"
            f"border: 2px solid {LINE}; border-left: 1px solid #fffef8; border-top: 1px solid #fffef8;"
            "border-right: 5px solid #c99462; border-bottom: 5px solid #c99462; border-radius: 10px;"
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
        self.progress_panel.setGeometry(646, 32, 218, 64)
        self.progress_panel.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #fffef8, stop:1 #f7e7ca);"
            "border: 1px solid #e1bd91; border-right: 4px solid #d29c67; border-bottom: 4px solid #d29c67; border-radius: 8px;"
        )
        self.progress_text = make_label(self.progress_panel, "", 18, 8, 168, 28, 13, 900)
        self.progress_track = QFrame(self.progress_panel)
        self.progress_track.setGeometry(18, 44, 180, 12)
        self.progress_track.setStyleSheet("background-color: #ffe2b8; border: 1px solid #c68d4f; border-radius: 5px;")
        self.progress_fill = QFrame(self.progress_track)
        self.progress_fill.setGeometry(0, 0, 60, 12)
        self.progress_fill.setStyleSheet(f"background-color: {MINT}; border: none; border-radius: 5px;")
        for child in self.left_panel.findChildren(QLabel):
            geom = child.geometry()
            if geom.x() == 118 and geom.y() == 20:
                child.hide()
            elif geom.x() == 118 and geom.y() == 60:
                child.hide()
        self.left_title_overlay = make_label(self.left_panel, "\u4ee3\u529e", 118, 20, 196, 42, 18, 900)
        self.left_title_overlay.setStyleSheet(
            "color: #10151b; border: none; font-family: 'Microsoft YaHei'; font-size: 18pt; font-weight: 900;"
        )
        self.left_title_overlay.raise_()
        self.left_subtitle_overlay = make_label(
            self.left_panel,
            "\u7ba1\u7406\u4f60\u7684\u4efb\u52a1\uff0c\u4fdd\u6301\u4e13\u6ce8\u4e0e\u597d\u5fc3\u60c5",
            118,
            60,
            450,
            32,
            12,
            700,
        )
        self.left_subtitle_overlay.setStyleSheet(
            "color: #10151b; border: none; font-family: 'Microsoft YaHei'; font-size: 12pt; font-weight: 700;"
        )
        self.left_subtitle_overlay.raise_()

        self.today_tab = PixelButton("今日任务（4）", self.left_panel, "#fffaf2")
        self.today_tab.setGeometry(18, 118, 244, 52)
        apply_button_icon(self.today_tab, "todo", 22)
        self.today_tab.clicked.connect(lambda: self._set_tab("today"))
        self.done_tab = PixelButton("已完成（1）", self.left_panel, "#fffaf2")
        self.done_tab.setGeometry(270, 124, 184, 46)
        apply_button_icon(self.done_tab, "completed", 22)
        self.done_tab.clicked.connect(lambda: self._set_tab("completed"))
        self.filter_button = PixelButton("筛选", self.left_panel, "#fffaf2")
        self.filter_button.setGeometry(628, 124, 112, 40)
        apply_button_icon(self.filter_button, "filter", 20)
        self.filter_button.clicked.connect(self._cycle_filter)
        self.sort_button = PixelButton("排序", self.left_panel, "#fffaf2")
        self.sort_button.setGeometry(756, 124, 104, 40)
        apply_button_icon(self.sort_button, "sort", 20)
        self.sort_button.clicked.connect(self._cycle_sort)

        self.date_icon = QLabel("", self.left_panel)
        self.date_icon.setGeometry(36, 188, 22, 22)
        self.date_icon.setAlignment(Qt.AlignCenter)
        self.date_icon.setStyleSheet("background: transparent; border: none;")
        apply_label_icon(self.date_icon, "calendar", 22)
        self.date_label = make_label(self.left_panel, "", 64, 184, 360, 32, 12, 800)

        self.list_panel = QScrollArea(self.left_panel)
        self.list_panel.setGeometry(28, 222, 826, 250)
        self.list_panel.setWidgetResizable(False)
        self.list_panel.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list_panel.setStyleSheet(
            "QScrollArea { background: transparent; border: none; }"
            "QScrollBar:vertical { background: #f1debd; width: 12px; margin: 6px 0 6px 0; border-radius: 5px; }"
            "QScrollBar::handle:vertical { background: #c89964; min-height: 24px; border-radius: 5px; }"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }"
        )
        self.list_content = QWidget()
        self.list_content.setStyleSheet("background: transparent; border: none;")
        self.list_panel.setWidget(self.list_content)

        self.input = QLineEdit(self.left_panel)
        self.input.setGeometry(40, 490, 642, 72)
        self.input.setPlaceholderText("＋  添加新任务...")
        self.input.setStyleSheet(
            "QLineEdit { background-color: #fffaf2; border: 2px dashed #bda890; border-radius: 7px;"
            "border-right: 3px dashed #92765c; border-bottom: 3px dashed #92765c;"
            "font-family: 'Microsoft YaHei'; font-size: 13pt; font-weight: 900; color: #10151b; padding-left: 18px; }"
        )
        self.input.returnPressed.connect(self._add_task)
        self.add_button = PixelButton("添加任务", self.left_panel, MINT, "white")
        self.add_button.setGeometry(702, 502, 136, 52)
        self.add_button.setStyleSheet(
            "QPushButton {"
            f"background-color: {MINT}; color: white;"
            "border: 2px solid #0f6f55;"
            "border-right: 4px solid #07523f;"
            "border-bottom: 4px solid #07523f;"
            "border-radius: 7px;"
            "font-family: 'Microsoft YaHei';"
            "font-size: 11pt;"
            "font-weight: 900;"
            "padding: 6px 10px;"
            "min-height: 34px;"
            "}"
            "QPushButton:hover { background-color: #22d9b4; color: white; }"
            "QPushButton:pressed { padding-left: 8px; padding-top: 8px; }"
        )
        self.add_button.clicked.connect(self._add_task)

    def _layout_tabs(self) -> None:
        if self.active_tab == "today":
            self.today_tab.setGeometry(18, 116, 252, 56)
            self.done_tab.setGeometry(280, 122, 176, 48)
        else:
            self.today_tab.setGeometry(18, 122, 176, 48)
            self.done_tab.setGeometry(204, 116, 252, 56)


    def _build_assistant_panel(self) -> None:
        self.right_shadow = pixel_shadow(self, 934, 120, 392, 568, 12, "#6f9ad4")
        self.right_panel = QFrame(self)
        self.right_panel.setGeometry(934, 120, 392, 568)
        self.right_panel.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #e7f2ff, stop:1 #d2e7ff);"
            "border: 3px solid #4a8ad9; border-left: 1px solid #dff0ff; border-top: 1px solid #dff0ff;"
            "border-right: 6px solid #2c70bf; border-bottom: 6px solid #2c70bf; border-radius: 12px;"
        )
        make_label(self.right_panel, "🐾  MoodPet 小助手  🐾", 70, 8, 280, 34, 13, 900)

        mood_card = QFrame(self.right_panel)
        mood_card.setGeometry(18, 52, 356, 128)
        mood_card.setStyleSheet(
            f"background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #fffef8, stop:1 {PANEL});"
            f"border: 2px solid {LINE}; border-left: 1px solid #fffef8; border-top: 1px solid #fffef8;"
            "border-right: 4px solid #c99462; border-bottom: 4px solid #c99462; border-radius: 9px;"
        )
        make_label(mood_card, "今日心情： 有点疲惫 😔", 22, 14, 310, 32, 14, 900)
        make_label(mood_card, "🐱", 28, 54, 54, 48, 25, 900)
        self.energy_track = QFrame(mood_card)
        self.energy_track.setGeometry(88, 70, 234, 16)
        self.energy_track.setStyleSheet("background-color: #ffe2b8; border: 1px solid #a16f3f; border-radius: 6px;")
        self.energy_fill = QFrame(self.energy_track)
        self.energy_fill.setGeometry(0, 0, 154, 16)
        self.energy_fill.setStyleSheet("background-color: #ffd34f; border-right: 4px solid #18b888; border-radius: 5px;")
        self.fatigue_label = make_label(mood_card, "", 88, 92, 184, 28, 10, 800)

        self.bubble = QLabel("", self.right_panel)
        self.bubble.setGeometry(26, 190, 292, 116)
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
        recommend.setGeometry(14, 466, 366, 86)
        recommend.setStyleSheet(
            f"background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #fffef8, stop:1 {PANEL});"
            f"border: 2px solid {LINE}; border-left: 1px solid #fffef8; border-top: 1px solid #fffef8;"
            "border-right: 4px solid #c99462; border-bottom: 4px solid #c99462; border-radius: 8px;"
        )
        make_label(recommend, "⭐  为你推荐", 18, 2, 160, 30, 12, 900)
        make_label(recommend, "●", 20, 36, 36, 34, 20, 900).setStyleSheet(
            "color: #f44336; border: none; font-family: 'Microsoft YaHei'; font-size: 20pt; font-weight: 900;"
        )
        make_label(recommend, "番茄钟专注 25 分钟", 60, 28, 176, 24, 10, 900)
        make_label(recommend, "专注一段，效率更高", 60, 51, 166, 20, 8, 700)
        self.focus_button = PixelButton("开始专注", recommend, MINT, "white")
        self.focus_button.setGeometry(228, 36, 128, 40)
        self.focus_button.setStyleSheet(
            "QPushButton {"
            f"background-color: {MINT}; color: white;"
            "border: 2px solid #0f6f55; border-right: 4px solid #07523f; border-bottom: 4px solid #07523f;"
            "border-radius: 7px; font-family: 'Microsoft YaHei'; font-size: 9pt; font-weight: 900;"
            "padding: 4px 8px;"
            "}"
            "QPushButton:hover { background-color: #22d9b4; }"
            "QPushButton:pressed { padding-left: 7px; padding-top: 6px; }"
        )
        self.focus_button.clicked.connect(self._focus_done)
        self.focus_time_label = make_label(recommend, "25:00", 246, 8, 92, 24, 11, 900)
        self.focus_time_label.setAlignment(Qt.AlignCenter)
        self.focus_time_label.setStyleSheet(
            "color: #0b735e; border: none; font-family: 'Microsoft YaHei'; font-size: 11pt; font-weight: 900;"
        )
        for child in recommend.findChildren(QLabel):
            geom = child.geometry()
            if geom.x() == 18 and geom.y() == 2:
                child.hide()
            elif geom.x() == 20 and geom.y() == 36:
                child.hide()
            elif geom.x() == 58 and geom.y() == 28:
                child.hide()
            elif geom.x() == 58 and geom.y() == 51:
                child.hide()
        self.recommend_title_overlay = make_label(recommend, "\u4e3a\u4f60\u63a8\u8350", 18, 2, 164, 30, 11, 900)
        self.recommend_title_overlay.setStyleSheet(
            "color: #10151b; border: none; font-family: 'Microsoft YaHei'; font-size: 11pt; font-weight: 900;"
        )
        self.recommend_title_overlay.raise_()
        self.recommend_icon_overlay = make_label(recommend, "●", 20, 36, 36, 34, 20, 900)
        self.recommend_icon_overlay.setStyleSheet(
            "color: #f44336; border: none; font-family: 'Microsoft YaHei'; font-size: 20pt; font-weight: 900;"
        )
        self.recommend_icon_overlay.raise_()
        self.recommend_focus_text = make_label(recommend, "\u756a\u8304\u949f\u4e13\u6ce8 25 \u5206\u949f", 58, 28, 180, 24, 9, 900)
        self.recommend_focus_text.setStyleSheet(
            "color: #10151b; border: none; font-family: 'Microsoft YaHei'; font-size: 9pt; font-weight: 900;"
        )
        self.recommend_focus_text.raise_()
        self.recommend_focus_hint = make_label(recommend, "\u4e13\u6ce8\u4e00\u6bb5\uff0c\u6548\u7387\u66f4\u9ad8", 58, 51, 172, 20, 8, 700)
        self.recommend_focus_hint.setStyleSheet(
            "color: #10151b; border: none; font-family: 'Microsoft YaHei'; font-size: 8pt; font-weight: 700;"
        )
        self.recommend_focus_hint.raise_()

    def _create_row(self, item: TodoItem, y: int) -> QFrame:
        row = QFrame(self.list_content)
        row.setGeometry(0, y, 826, 58)
        bg = "#edf8e6" if item.completed else "#fffaf2"
        row.setStyleSheet(
            f"background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #fffef7, stop:1 {bg});"
            "border: 1px solid #e1bd91; border-left: 1px solid #fffdf8; border-top: 1px solid #fffdf8;"
            "border-right: 4px solid #d0a06d; border-bottom: 4px solid #d0a06d; border-radius: 8px;"
        )

        check = QPushButton("", row)
        check.setGeometry(18, 14, 32, 32)
        check.setCursor(Qt.PointingHandCursor)
        if item.completed:
            apply_button_icon(check, "completed", 20, "white")
        check.setStyleSheet(
            "QPushButton { background-color: "
            + (MINT if item.completed else "#fffaf2")
            + "; color: white; border: 2px solid #d9a26f; border-radius: 5px;"
            "font-family: 'Microsoft YaHei'; font-size: 16pt; font-weight: 900; }"
        )
        check.clicked.connect(lambda checked=False, item_id=item.id: self._toggle_completed(item_id))

        title = make_label(row, item.title, 68, 12, 290, 32, 11, 900)
        if item.completed:
            title.setStyleSheet(
                "color: #222; border: none; font-family: 'Microsoft YaHei'; font-size: 11pt; font-weight: 900;"
            )

        chip_color = CATEGORY_COLORS.get(item.category, BLUE)
        chip = QLabel(item.category, row)
        chip.setGeometry(364, 16, 54, 26)
        chip.setAlignment(Qt.AlignCenter)
        chip.setStyleSheet(
            f"background-color: #fff7e9; color: {chip_color}; border: 1px solid {chip_color};"
            "border-radius: 4px; font-family: 'Microsoft YaHei'; font-size: 9pt; font-weight: 900;"
        )

        status = item.completed_at + " 完成" if item.completed else f"{item.due_time} 截止"
        status_label = make_label(row, status, 578, 12, 178, 32, 9, 700)
        status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        star = QPushButton("", row)
        star.setGeometry(780, 12, 32, 34)
        star.setCursor(Qt.PointingHandCursor)
        apply_button_icon(star, "star", 24, GOLD if item.starred else "#d0935f")
        star.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {GOLD if item.starred else '#d0935f'};"
            "border: none; font-family: 'Microsoft YaHei'; font-size: 19pt; font-weight: 900; }}"
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
        self.focus_remaining_seconds = 25 * 60
        self._update_focus_timer_label()
        self.focus_button.setText("专注中")
        self.focus_button.setEnabled(False)
        self.focus_timer.start(1000)

    def _tick_focus_timer(self) -> None:
        if self.focus_remaining_seconds > 0:
            self.focus_remaining_seconds -= 1
        self._update_focus_timer_label()
        if self.focus_remaining_seconds <= 0:
            self.focus_timer.stop()
            self.focus_button.setText("开始专注")
            self.focus_button.setEnabled(True)
            self.bubble.setText("番茄钟完成啦，给自己一点奖励吧 ✨")

    def _update_focus_timer_label(self) -> None:
        minutes, seconds = divmod(max(0, self.focus_remaining_seconds), 60)
        self.focus_time_label.setText(f"{minutes:02d}:{seconds:02d}")

    def refresh(self) -> None:
        for frame in self.row_frames:
            frame.setParent(None)
            frame.deleteLater()
        self.row_frames = []

        done_count = sum(1 for item in self.todos if item.completed)
        total_count = len(self.todos)
        done_visible = sum(1 for item in self.todos if item.completed)
        self.today_tab.setText(f"今日任务（{total_count}）")
        self.done_tab.setText(f"已完成（{done_visible}）")
        apply_button_icon(self.today_tab, "todo", 22)
        apply_button_icon(self.done_tab, "completed", 22)
        self.progress_text.setText(completion_text(self.todos))
        self.progress_fill.setFixedWidth(max(0, min(172, int(172 * completion_ratio(self.todos)))))
        self.date_label.setText(today_label())
        filter_specs = {
            "time": ("筛选", "filter"),
            "category": ("分类", "sort"),
            "starred": ("星标", "star"),
        }
        filter_text, filter_icon = filter_specs[self.sort_mode]
        self.filter_button.setText(filter_text)
        apply_button_icon(self.filter_button, filter_icon, 20)
        apply_button_icon(self.sort_button, "sort", 20)
        self._layout_tabs()

        self.today_tab.setStyleSheet(self._tab_style(self.active_tab == "today"))
        self.done_tab.setStyleSheet(self._tab_style(self.active_tab == "completed"))

        rows = visible_todos(self.todos, self.active_tab, self.sort_mode)
        self.list_content.setFixedSize(826, max(250, max(1, len(rows)) * 60))
        self.list_panel.verticalScrollBar().setValue(0)
        for index, item in enumerate(rows):
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
            f"background-color: {bg}; color: #102943; border: 2px solid {border};"
            "border-right: 4px solid #8b6a4e; border-bottom: 4px solid #8b6a4e; border-radius: 8px;"
            "font-family: 'Microsoft YaHei'; font-size: 11pt; font-weight: 900; padding: 6px 9px;"
            "}"
            "QPushButton:hover { background-color: #fffaf2; }"
        )
