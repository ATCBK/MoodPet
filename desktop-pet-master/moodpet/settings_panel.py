from dataclasses import replace
from pathlib import Path
from typing import Callable, Optional

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QFont, QMovie
from PyQt5.QtWidgets import QFrame, QLabel, QPushButton, QSlider, QWidget

from moodpet.pixel_icons import apply_button_icon, apply_label_icon
from moodpet.settings_state import (
    FREQUENCY_OPTIONS,
    JUMP_TARGET_OPTIONS,
    SettingsState,
    apply_frequency,
    apply_jump_target,
    frequency_label,
    jump_target_label,
)


INK = "#10151b"
NAVY = "#073040"
TEAL = "#43d0bf"
DEEP_TEAL = "#168f84"
CREAM = "#fff1da"
PANEL = "#fff8ec"
LINE = "#dfc39b"
SOFT = "#fffaf2"
PINK = "#ff6d78"
LILAC = "#eee5ff"
MINT = "#e4fff4"
RED_SOFT = "#fff0ee"
GLOW = "#fffdf8"
DEEP = "#0d2538"
DEEP_MID = "#183654"


def raised_surface(fill: str, border: str, shadow: str = DEEP, highlight: str = GLOW) -> str:
    return (
        f"background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {highlight}, stop:0.18 {fill}, stop:1 {fill});"
        f"border: 2px solid {border};"
        f"border-right: 5px solid {shadow};"
        f"border-bottom: 5px solid {shadow};"
        "border-radius: 10px;"
    )


def make_label(parent: QWidget, text: str, x: int, y: int, w: int, h: int, size: int = 12, weight: int = 700) -> QLabel:
    label = QLabel(text, parent)
    label.setGeometry(x, y, w, h)
    label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    label.setWordWrap(True)
    font = QFont("Microsoft YaHei")
    font.setPixelSize(size)
    font.setWeight(weight)
    label.setFont(font)
    label.setStyleSheet(f"color: {INK}; border: none; background: transparent;")
    return label


class SegmentButton(QPushButton):
    def __init__(self, text: str, parent: QWidget) -> None:
        super().__init__(text, parent)
        self._base_color = SOFT
        self._base_border = LINE
        self.setCursor(Qt.PointingHandCursor)
        font = QFont("Microsoft YaHei")
        font.setPixelSize(15)
        font.setWeight(900)
        self.setFont(font)
        self.set_active(False)

    def set_active(self, active: bool) -> None:
        bg = "#dff8ec" if active else self._base_color
        border = DEEP_TEAL if active else self._base_border
        self.setStyleSheet(
            "QPushButton {"
            f"background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {GLOW}, stop:0.24 {bg}, stop:1 {bg});"
            f"color: {INK}; border: 2px solid {border}; border-right: 4px solid {border}; border-bottom: 4px solid {border}; border-radius: 8px;"
            "padding: 4px 8px;"
            "}"
            "QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #fffefb, stop:0.24 #fff6d7, stop:1 #ffeeb6); }"
            "QPushButton:pressed { padding-left: 10px; padding-top: 6px; border-right-width: 2px; border-bottom-width: 2px; }"
        )


class PixelButton(QPushButton):
    def __init__(self, text: str, parent: QWidget, color: str = SOFT, border: str = LINE) -> None:
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self._color = color
        self._border = border
        font = QFont("Microsoft YaHei")
        font.setPixelSize(17)
        font.setWeight(900)
        self.setFont(font)
        self.setStyleSheet(
            "QPushButton {"
            f"background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {GLOW}, stop:0.28 {color}, stop:1 {color});"
            f"color: {INK}; border: 2px solid {border}; border-right: 5px solid {border}; border-bottom: 5px solid {border}; border-radius: 8px;"
            "padding: 8px 10px;"
            "}"
            "QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #fffefb, stop:0.28 #fff6d7, stop:1 #ffeeb6); }"
            "QPushButton:pressed { padding-left: 12px; padding-top: 10px; border-right-width: 2px; border-bottom-width: 2px; }"
        )

    def set_selected(self, selected: bool) -> None:
        bg = "#dff8ec" if selected else self._color
        border = DEEP_TEAL if selected else self._border
        self.setStyleSheet(
            "QPushButton {"
            f"background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {GLOW}, stop:0.28 {bg}, stop:1 {bg});"
            f"color: {INK}; border: 2px solid {border}; border-right: 5px solid {border}; border-bottom: 5px solid {border}; border-radius: 8px;"
            "padding: 8px 10px;"
            "}"
            "QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #fffefb, stop:0.28 #fff6d7, stop:1 #ffeeb6); }"
            "QPushButton:pressed { padding-left: 12px; padding-top: 10px; border-right-width: 2px; border-bottom-width: 2px; }"
        )


class SectionCard(QFrame):
    def __init__(self, parent: QWidget, y: int, h: int, icon_feature: str, title: str, body: str) -> None:
        super().__init__(parent)
        self.setGeometry(18, y, 500, h)
        self.setStyleSheet(
            f"QFrame {{"
            f"background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {GLOW}, stop:0.12 {PANEL}, stop:1 {PANEL});"
            f"border: 2px solid {LINE};"
            f"border-right: 5px solid {DEEP};"
            f"border-bottom: 5px solid {DEEP};"
            "border-radius: 14px;"
            "}}"
        )
        self.icon_label = make_label(self, "", 22, 18, 58, 52, 25, 900)
        apply_label_icon(self.icon_label, icon_feature, 32)
        make_label(self, title, 82, 18, 330, 32, 16, 900)
        body_height = 72 if h <= 140 else 46
        self.body_label = make_label(self, body, 82, 52, 380, body_height, 11, 700)


class SettingsPanelWindow(QWidget):
    def __init__(
        self,
        base_dir: Path,
        get_camera_enabled: Callable[[], bool],
        toggle_recognition: Callable[[], None],
        parent: Optional[QWidget] = None,
        on_settings_change: Optional[Callable[[SettingsState], None]] = None,
        open_target: Optional[Callable[[str], None]] = None,
    ) -> None:
        super().__init__(parent)
        self.base_dir = base_dir
        self.get_camera_enabled = get_camera_enabled
        self.toggle_recognition = toggle_recognition
        self.on_settings_change = on_settings_change
        self.open_target = open_target
        self.state = SettingsState(camera_enabled=get_camera_enabled())
        self.setWindowTitle("主动气泡交互机制")
        self.setFixedSize(540, 924)
        self.setStyleSheet(f"background-color: {CREAM};")
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        self.shell = QFrame(self)
        self.shell.setGeometry(8, 8, 524, 908)
        self.shell.setStyleSheet(
            f"QFrame {{"
            f"background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {GLOW}, stop:0.08 {CREAM}, stop:1 {CREAM});"
            f"border: 4px solid {NAVY};"
            f"border-right: 7px solid {DEEP};"
            f"border-bottom: 7px solid {DEEP};"
            "border-radius: 18px;"
            "}}"
        )

        header = QFrame(self.shell)
        header.setGeometry(0, 0, 524, 66)
        header.setStyleSheet(
            f"QFrame {{ background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #86efe1, stop:0.45 {TEAL}, stop:1 {DEEP_TEAL}); border: none; border-bottom: 4px solid {NAVY};"
            "border-top-left-radius: 13px; border-top-right-radius: 13px; }"
        )
        make_label(header, "主动气泡交互机制", 42, 7, 390, 46, 30, 900)
        close = QPushButton("", header)
        close.setGeometry(466, 12, 38, 38)
        close.setCursor(Qt.PointingHandCursor)
        apply_button_icon(close, "close", 24)
        close_font = QFont("Microsoft YaHei")
        close_font.setPixelSize(28)
        close_font.setWeight(900)
        close.setFont(close_font)
        close.setStyleSheet(
            f"background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ff98a0, stop:0.45 {PINK}, stop:1 #db5660); color: white; border: 3px solid {NAVY}; border-right: 5px solid {NAVY}; border-bottom: 5px solid {NAVY}; border-radius: 8px;"
            "padding: 0;"
        )
        close.clicked.connect(self.hide)

        self.emotion_card = SectionCard(
            self.shell,
            84,
            222,
            "camera",
            "情绪检测触发",
            "通过摄像头识别情绪，自动匹配气泡建议。",
        )
        self._build_emotion_options()

        self.frequency_card = SectionCard(
            self.shell,
            324,
            166,
            "bubble",
            "气泡频率设置",
            "智能控制触发频率，避免打扰。",
        )
        self._build_frequency_controls()

        self.jump_card = SectionCard(
            self.shell,
            508,
            184,
            "message",
            "点击跳转目标",
            "点击气泡可快速跳转到目标页面。",
        )
        self._build_jump_controls()

        self.dnd_card = SectionCard(
            self.shell,
            710,
            132,
            "privacy",
            "不打扰原则",
            "同一情绪短时间内不重复弹出；\n夜间 / 专注模式自动降低频率；\n可以随时在设置中调整。",
        )
        self.dnd_card.body_label.setGeometry(82, 52, 380, 72)

        footer = QFrame(self.shell)
        footer.setGeometry(0, 860, 524, 48)
        footer.setStyleSheet(
            f"QFrame {{ background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #12324f, stop:1 {NAVY}); border: none; border-top: 4px solid #071927;"
            "border-bottom-left-radius: 13px; border-bottom-right-radius: 13px; }"
        )
        pet = QLabel(footer)
        pet.setGeometry(28, -10, 58, 58)
        movie = QMovie(str(self.base_dir / "pet" / "init" / "stay.gif"))
        movie.setScaledSize(QSize(56, 56))
        pet.setMovie(movie)
        movie.start()
        self.footer_pet_movie = movie
        self.mode_label = make_label(footer, "", 92, 8, 380, 28, 16, 900)
        self.mode_label.setStyleSheet("color: #70e4c7; border: none; background: transparent;")

    def _build_emotion_options(self) -> None:
        options = [("💗", "疲惫"), ("☺", "开心"), ("☹", "低落"), ("☻", "平静")]
        for index, (icon, label) in enumerate(options):
            x = 34 + index * 110
            tile = QFrame(self.emotion_card)
            tile.setGeometry(x, 120, 96, 78)
            tile.setStyleSheet(
                f"background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {GLOW}, stop:0.25 {SOFT}, stop:1 {SOFT});"
                f"border: 2px solid {LINE}; border-right: 4px solid {DEEP_MID}; border-bottom: 4px solid {DEEP_MID}; border-radius: 10px;"
            )
            emoji = QLabel(icon, tile)
            emoji.setGeometry(0, 8, 96, 30)
            emoji.setAlignment(Qt.AlignCenter)
            emoji_font = QFont("Microsoft YaHei")
            emoji_font.setPixelSize(28)
            emoji_font.setWeight(900)
            emoji.setFont(emoji_font)
            emoji.setStyleSheet("border: none; background: transparent;")
            text = QLabel(label, tile)
            text.setGeometry(0, 42, 96, 26)
            text.setAlignment(Qt.AlignCenter)
            text_font = QFont("Microsoft YaHei")
            text_font.setPixelSize(18)
            text_font.setWeight(900)
            text.setFont(text_font)
            text.setStyleSheet(f"color: {INK}; border: none; background: transparent;")

        self.camera_button = PixelButton("开启识别", self.emotion_card, MINT, DEEP_TEAL)
        self.camera_button.setGeometry(364, 22, 102, 42)
        apply_button_icon(self.camera_button, "camera", 24)
        self.camera_button.clicked.connect(self._toggle_camera)
        self.camera_status = make_label(self.emotion_card, "", 82, 90, 288, 28, 14, 900)
        self.camera_status.setStyleSheet(
            f"color: {DEEP_TEAL}; background: {GLOW}; border: 1px solid {LINE}; border-right: 4px solid {DEEP_TEAL}; border-bottom: 4px solid {DEEP_TEAL}; border-radius: 8px; padding-left: 10px;"
        )

    def _build_frequency_controls(self) -> None:
        self.frequency_slider = QSlider(Qt.Horizontal, self.frequency_card)
        self.frequency_slider.setGeometry(36, 96, 426, 30)
        self.frequency_slider.setRange(0, 2)
        self.frequency_slider.setSingleStep(1)
        self.frequency_slider.setPageStep(1)
        self.frequency_slider.setTickInterval(1)
        self.frequency_slider.setTickPosition(QSlider.TicksBelow)
        self.frequency_slider.setStyleSheet(
            "QSlider::groove:horizontal { height: 12px; background: #d8c4a6; border: 1px solid #b99a6a; border-radius: 6px; }"
            f"QSlider::sub-page:horizontal {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {DEEP_TEAL}, stop:1 {TEAL}); border-radius: 6px; }}"
            f"QSlider::handle:horizontal {{ background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #8bf0e4, stop:1 {TEAL}); border: 3px solid {NAVY}; width: 26px; margin: -8px 0; border-radius: 13px; }}"
        )
        self.frequency_slider.valueChanged.connect(self._select_frequency_index)
        self.frequency_buttons = {}
        for index, (key, label, _description) in enumerate(FREQUENCY_OPTIONS):
            button = SegmentButton(label, self.frequency_card)
            button.setGeometry(28 + index * 157, 126, 124, 30)
            button.clicked.connect(lambda checked=False, idx=index: self._select_frequency_index(idx))
            self.frequency_buttons[key] = button

    def _build_jump_controls(self) -> None:
        self.target_buttons = {}
        specs = {
            "todo": ("去待办\n进入待办页", 32, RED_SOFT, "#e27f7b", "todo"),
            "games": ("去小游戏\n放松一下", 252, LILAC, "#9a86d9", "games"),
        }
        for target_id, (text, x, color, border, icon_feature) in specs.items():
            button = PixelButton(text, self.jump_card, color, border)
            button.setGeometry(x, 96, 204, 70)
            apply_button_icon(button, icon_feature, 24)
            button.clicked.connect(lambda checked=False, selected=target_id: self._select_target(selected))
            self.target_buttons[target_id] = button

    def _toggle_camera(self) -> None:
        self.toggle_recognition()
        self.refresh()

    def _select_frequency_index(self, index: int) -> None:
        if 0 <= index < len(FREQUENCY_OPTIONS):
            self.state = apply_frequency(self.state, FREQUENCY_OPTIONS[index][0])
            self._notify()
            self.refresh()

    def _select_target(self, target_id: str) -> None:
        self.state = apply_jump_target(self.state, target_id)
        self._notify()
        if self.open_target is not None:
            self.open_target(target_id)
        self.refresh()

    def _notify(self) -> None:
        if self.on_settings_change is not None:
            self.on_settings_change(self.state)

    def refresh(self) -> None:
        self.state = replace(self.state, camera_enabled=self.get_camera_enabled())
        frequency_keys = [value for value, _, _ in FREQUENCY_OPTIONS]
        index = frequency_keys.index(self.state.bubble_frequency)
        self.frequency_slider.blockSignals(True)
        self.frequency_slider.setValue(index)
        self.frequency_slider.blockSignals(False)
        for key, button in self.frequency_buttons.items():
            button.set_active(key == self.state.bubble_frequency)
        for target_id, button in self.target_buttons.items():
            button.set_selected(target_id == self.state.jump_target)
        self.camera_button.setText("关闭识别" if self.state.camera_enabled else "开启识别")
        self.camera_button.set_selected(self.state.camera_enabled)
        self.camera_status.setText("摄像头后台识别中" if self.state.camera_enabled else "摄像头未开启")
        self.mode_label.setText(f"当前模式：{frequency_label(self.state.bubble_frequency)}｜{jump_target_label(self.state.jump_target)}")
