import threading
import queue
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from PyQt5.QtCore import QPoint, QRect, QSize, Qt, QTimer
from PyQt5.QtGui import QColor, QFont, QIcon, QMovie, QPainter, QPainterPath, QPen, QPixmap
from PyQt5.QtWidgets import QFrame, QLabel, QPushButton, QWidget

from moodpet.mini_game_state import (
    MiniGameState,
    available_choices,
    build_default_game,
    build_story_render_states,
    choose_event,
    collected_count_text,
    complete_interaction,
    continue_story,
    current_node,
    progress_text,
    restart_game,
)
from moodpet.emotion import EmotionState, build_emotion_state
from moodpet.env_paths import resolve_env_path
from moodpet.pixel_icons import apply_button_icon, apply_label_icon
from moodpet.side_nav import build_pet_sidebar
from moodpet.seedream_image import SeedreamImageService, build_seedream_image_service
from moodpet.story_generation import StoryGenerationService, build_story_generation_service


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
FONT_FAMILY = "Microsoft YaHei"
SHADOW = "#b58a61"
SHADOW_DEEP = "#8d6a4a"
LIGHT_EDGE = "#fffdf7"
CARD_EDGE = "#d0aa7c"
BLUE_STAMP = "#2b6fd6"
BLUE_STAMP_LIGHT = "#d9ebff"
CLOCK_BLUE = "#5d7ea5"
CLOCK_LIGHT = "#ebf3ff"

CLUE_ICON_MAP = {
    "stamp": ("story_stamp", BLUE_STAMP, BLUE_STAMP_LIGHT),
    "clock": ("story_clock", CLOCK_BLUE, CLOCK_LIGHT),
    "address": ("note", "#b57d4f", "#fff2dc"),
    "mint_scent": ("heart", "#1ba089", "#defcf6"),
    "return_date": ("calendar", "#9e71b5", "#f1e6ff"),
}


def raised_panel_style(fill: str, border: str = CARD_EDGE, radius: int = 10, shadow: str = SHADOW_DEEP) -> str:
    return (
        "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
        f"stop:0 {LIGHT_EDGE}, stop:0.16 {fill}, stop:1 {fill});"
        f"border: 2px solid {border};"
        f"border-left: 1px solid {LIGHT_EDGE};"
        f"border-top: 1px solid {LIGHT_EDGE};"
        f"border-right: 4px solid {shadow};"
        f"border-bottom: 4px solid {shadow};"
        f"border-radius: {radius}px;"
    )


def card_shadow(parent: QWidget, x: int, y: int, w: int, h: int, radius: int = 10, color: str = SHADOW) -> QFrame:
    shadow = QFrame(parent)
    shadow.setGeometry(x + 6, y + 6, w, h)
    shadow.setStyleSheet(f"background-color: {color}; border: none; border-radius: {radius}px;")
    shadow.lower()
    return shadow


def _pixmap(size: int) -> QPixmap:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    return pixmap


def render_stamp_pixmap(size: int = 44) -> QPixmap:
    pixmap = _pixmap(size)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    inset = 4
    path = QPainterPath()
    path.addRoundedRect(inset + 2, inset + 2, size - 12, size - 12, 6, 6)
    painter.fillPath(path, QColor(16, 34, 54, 32))
    painter.translate(0, 0)
    stamp = QPainterPath()
    x0 = inset + 8
    y0 = inset + 8
    w = size - 22
    h = size - 22
    stamp.moveTo(x0 + 4, y0)
    stamp.lineTo(x0 + w - 4, y0)
    stamp.lineTo(x0 + w, y0 + 4)
    stamp.lineTo(x0 + w, y0 + h - 4)
    stamp.lineTo(x0 + w - 4, y0 + h)
    stamp.lineTo(x0 + 4, y0 + h)
    stamp.lineTo(x0, y0 + h - 4)
    stamp.lineTo(x0, y0 + 4)
    stamp.closeSubpath()
    painter.setPen(QPen(QColor("#1f4ea0"), 2))
    painter.setBrush(QColor("#cfe2ff"))
    painter.drawPath(stamp)
    painter.setPen(QPen(QColor("#fff9ff"), 1))
    for idx in range(5):
        painter.drawLine(x0 + 2 + idx * 6, y0 + 2, x0 + 2 + idx * 6, y0 + 6)
        painter.drawLine(x0 + 2 + idx * 6, y0 + h - 6, x0 + 2 + idx * 6, y0 + h - 2)
    painter.setPen(QPen(QColor("#275cc2"), 1))
    painter.drawLine(x0 + 6, y0 + 15, x0 + w - 6, y0 + 15)
    painter.drawLine(x0 + 6, y0 + 22, x0 + w - 10, y0 + 22)
    painter.setPen(QPen(QColor("#2f66cf"), 4))
    painter.drawLine(x0 + 9, y0 + 28, x0 + 22, y0 + 28)
    painter.end()
    return pixmap


def render_clock_pixmap(size: int = 44) -> QPixmap:
    pixmap = _pixmap(size)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    center = size / 2
    radius = size / 2 - 5
    painter.setPen(QPen(QColor("#4d6a8d"), 2))
    painter.setBrush(QColor("#eef5ff"))
    painter.drawEllipse(5, 5, size - 10, size - 10)
    painter.setPen(QPen(QColor("#46607f"), 2))
    painter.drawEllipse(9, 9, size - 18, size - 18)
    painter.setPen(QPen(QColor("#4d6a8d"), 2))
    painter.drawLine(int(center), 7, int(center), 3)
    painter.drawLine(size - 9, int(center), size - 4, int(center))
    painter.setPen(QPen(QColor("#26486e"), 3))
    painter.drawLine(int(center), int(center), int(center), int(center - radius * 0.35))
    painter.drawLine(int(center), int(center), int(center + radius * 0.22), int(center + radius * 0.12))
    painter.setPen(QPen(QColor("#2b3140"), 2))
    painter.drawLine(size - 8, 8, size - 8, 12)
    painter.drawLine(size - 12, 8, size - 12, 12)
    painter.end()
    return pixmap


def render_envelope_pixmap(size: int = 68, fill: str = "#fffaf2", line: str = "#b99169", accent: str = "#ff6a7a") -> QPixmap:
    pixmap = _pixmap(size)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    w = size - 10
    h = size - 18
    x = 5
    y = 8
    body = QPainterPath()
    body.addRoundedRect(x + 2, y + 3, w - 4, h - 6, 6, 6)
    painter.fillPath(body, QColor(16, 34, 54, 26))
    envelope = QPainterPath()
    envelope.moveTo(x + 4, y + 8)
    envelope.lineTo(x + w / 2, y + h - 8)
    envelope.lineTo(x + w - 4, y + 8)
    envelope.lineTo(x + w - 4, y + h - 8)
    envelope.lineTo(x + 4, y + h - 8)
    envelope.closeSubpath()
    painter.setPen(QPen(QColor(line), 2))
    painter.setBrush(QColor(fill))
    painter.drawPath(envelope)
    painter.setPen(QPen(QColor("#dfc39d"), 1.5))
    mid_x = int(x + w / 2)
    bottom_y = int(y + h - 10)
    painter.drawLine(int(x + 6), int(y + 11), mid_x, bottom_y)
    painter.drawLine(int(x + w - 6), int(y + 11), mid_x, bottom_y)
    painter.setBrush(QColor(accent))
    painter.setPen(QPen(QColor("#b84d61"), 1))
    painter.drawRect(x + w - 16, y + 2, 10, 12)
    painter.end()
    return pixmap


def render_paper_stack_pixmap(size: int = 96) -> QPixmap:
    pixmap = _pixmap(size)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    cards = [
        (12, 34, -14, "#ffe6e0", "#c79684"),
        (26, 18, 9, "#eef6ff", "#89a8d0"),
        (34, 42, 13, "#fff1d8", "#caa15e"),
    ]
    for dx, dy, angle, fill, border in cards:
        painter.save()
        painter.translate(dx + 24, dy + 24)
        painter.rotate(angle)
        painter.translate(-(dx + 24), -(dy + 24))
        path = QPainterPath()
        path.addRoundedRect(dx, dy, 48, 40, 5, 5)
        painter.fillPath(path, QColor(10, 20, 32, 24))
        painter.setPen(QPen(QColor(border), 2))
        painter.setBrush(QColor(fill))
        painter.drawPath(path)
        painter.setPen(QPen(QColor(border), 1))
        painter.drawLine(dx + 10, dy + 12, dx + 34, dy + 12)
        painter.drawLine(dx + 10, dy + 20, dx + 28, dy + 20)
        painter.restore()
    painter.setPen(QPen(QColor("#e8a2a8"), 1.8))
    painter.setBrush(Qt.NoBrush)
    painter.drawRect(8, 8, size - 16, size - 16)
    painter.end()
    return pixmap


def render_placeholder_pixmap(size: int = 44) -> QPixmap:
    pixmap = _pixmap(size)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    rect = QPainterPath()
    rect.addRoundedRect(6, 6, size - 12, size - 12, 5, 5)
    painter.fillPath(rect, QColor(10, 20, 32, 16))
    painter.setPen(QPen(QColor("#c7a789"), 2, Qt.DashLine))
    painter.setBrush(QColor("#fff8ef"))
    painter.drawPath(rect)
    painter.setPen(QPen(QColor("#a57d58"), 1))
    painter.setFont(QFont(FONT_FAMILY, max(10, size // 2), 900))
    painter.drawText(QRect(6, 6, size - 12, size - 12), Qt.AlignCenter, "？")
    painter.end()
    return pixmap


def label(parent: QWidget, text: str, geometry: Tuple[int, int, int, int], size: int = 12, weight: int = 700) -> QLabel:
    item = QLabel(text, parent)
    item.setGeometry(*geometry)
    item.setWordWrap(True)
    item.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    item.setFont(QFont(FONT_FAMILY, size, weight))
    item.setStyleSheet(f"color: {INK}; border: none; background: transparent;")
    return item


def single_line_label(parent: QWidget, text: str, geometry: Tuple[int, int, int, int], size: int = 12, weight: int = 700) -> QLabel:
    item = label(parent, text, geometry, size, weight)
    item.setWordWrap(False)
    return item


def set_elided_label_text(item: QLabel, text: str) -> None:
    available_width = max(0, item.width() - 4)
    item.setText(item.fontMetrics().elidedText(text, Qt.ElideRight, available_width))
    item.setToolTip(text)


class PixelButton(QPushButton):
    def __init__(self, text: str, parent: QWidget, color: str = PANEL, text_color: str = INK) -> None:
        super().__init__(text, parent)
        self.base_color = color
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(
            "QPushButton {"
            f"background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #fffaf4, stop:0.18 {color}, stop:1 {color});"
            f"color: {text_color};"
            f"border: 2px solid {CARD_EDGE};"
            f"border-left: 1px solid {LIGHT_EDGE};"
            f"border-top: 1px solid {LIGHT_EDGE};"
            f"border-right: 4px solid {SHADOW_DEEP};"
            f"border-bottom: 4px solid {SHADOW_DEEP};"
            "border-radius: 7px;"
            "padding: 7px 12px;"
            "text-align: left;"
            "}"
            "QPushButton:hover { background-color: #fffaf2; }"
            "QPushButton:pressed { padding-left: 13px; padding-top: 8px; }"
        )
        self.setFont(QFont(FONT_FAMILY, 10, 900))


class PostalScene(QWidget):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.caption = ""
        self.image_path: Optional[Path] = None
        self.scene_pixmap = QPixmap()

    def set_caption(self, caption: str) -> None:
        self.caption = caption
        self.update()

    def set_image_path(self, image_path: Optional[Path]) -> None:
        self.image_path = image_path
        self.scene_pixmap = QPixmap(str(image_path)) if image_path else QPixmap()
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)
        rect = self.rect().adjusted(2, 2, -2, -2)
        painter.fillRect(rect, QColor("#20334c"))

        if not self.scene_pixmap.isNull():
            image_rect = QRect(rect.left(), rect.top(), rect.width(), max(0, rect.height() - 92))
            scaled = self.scene_pixmap.scaled(image_rect.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            source_x = max(0, (scaled.width() - image_rect.width()) // 2)
            source_y = max(0, (scaled.height() - image_rect.height()) // 2)
            painter.drawPixmap(image_rect, scaled, QRect(source_x, source_y, image_rect.width(), image_rect.height()))
        else:
            for y, color in [(0, "#8c5c80"), (44, "#d78a77"), (88, "#f3b27a"), (132, "#644e69")]:
                painter.fillRect(rect.left(), rect.top() + y, rect.width(), 48, QColor(color))
            painter.fillRect(rect.left(), rect.top() + 156, rect.width(), rect.height() - 156, QColor("#2a273a"))
            painter.fillRect(rect.left() + 26, rect.top() + 44, 220, 182, QColor("#17263a"))
            painter.fillRect(rect.left() + 38, rect.top() + 56, 196, 158, QColor("#f0a36d"))
            painter.fillRect(rect.left() + 44, rect.top() + 62, 184, 146, QColor("#6c6a95"))

        painter.setPen(QPen(QColor("#071927"), 4))
        painter.drawRect(rect)

        painter.fillRect(rect.left(), rect.bottom() - 92, rect.width(), 90, QColor("#fff1da"))
        painter.setPen(QColor(INK))
        painter.setFont(QFont(FONT_FAMILY, 11, QFont.Bold))
        painter.drawText(
            QRect(rect.left() + 18, rect.bottom() - 84, rect.width() - 36, 72),
            Qt.AlignLeft | Qt.AlignVCenter | Qt.TextWordWrap,
            self.caption,
        )


class DraggableEnvelope(QLabel):
    def __init__(self, parent: QWidget, drop_rect: QRect, on_dropped) -> None:
        super().__init__("", parent)
        self.drop_rect = drop_rect
        self.on_dropped = on_dropped
        self.drag_offset = QPoint(0, 0)
        self.home = QPoint(34, 52)
        self.setGeometry(self.home.x(), self.home.y(), 70, 52)
        self.setAlignment(Qt.AlignCenter)
        self.setCursor(Qt.OpenHandCursor)
        self.setPixmap(render_envelope_pixmap(70))
        self.setStyleSheet("background: transparent; border: none;")

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
    def __init__(
        self,
        base_dir: Path,
        parent: Optional[QWidget] = None,
        open_target: Optional[Callable[[str], None]] = None,
        emotion_state: Optional[EmotionState] = None,
        generate_story: bool = True,
        preload_story_assets: bool = True,
    ) -> None:
        super().__init__(parent)
        self.base_dir = base_dir
        self.open_target = open_target or (lambda module_id: None)
        self.emotion_state = emotion_state or build_emotion_state("neutral")
        self.generate_story = generate_story
        self.preload_story_assets = preload_story_assets
        self.state = build_default_game()
        self.initial_story_state = self.state
        self.choice_buttons: List[PixelButton] = []
        self.env_path = resolve_env_path(base_dir)
        self.choice_image_service: Optional[SeedreamImageService] = build_seedream_image_service(base_dir, self.env_path)
        self.story_generation_service: StoryGenerationService = build_story_generation_service(base_dir, self.env_path)
        self.choice_image_paths = {}
        self.choice_image_loading = set()
        self.choice_image_errors = {}
        self.node_image_paths = {}
        self.node_image_loading = set()
        self.node_image_errors = {}
        self.selected_choice_image_key = ""
        self.selected_choice_image_path: Optional[Path] = None
        self._image_lock = threading.Lock()
        self.story_loading = self.generate_story
        self.story_generation_queue: "queue.Queue" = queue.Queue(maxsize=1)
        self.story_generation_timer = QTimer(self)
        self.story_generation_timer.timeout.connect(self._poll_story_generation_result)
        self.story_generation_timer.start(100)
        self.story_generation_request_id = 0
        self.story_assets_primed = False
        self.clue_cards: List[QFrame] = []
        self.clue_card_icons: List[QLabel] = []
        self.clue_card_titles: List[QLabel] = []
        self.reward_rows: List[QLabel] = []
        self.setWindowTitle("MoodPet 小游戏")
        self.setFixedSize(1360, 760)
        self.setStyleSheet(f"background-color: {CREAM};")
        self._build_ui()
        self._style_top_chrome()
        self.choice_image_timer = QTimer(self)
        self.choice_image_timer.timeout.connect(self._refresh_choice_images)
        self.choice_image_timer.start(100)
        self.refresh()
        if self.generate_story:
            self._start_story_generation()
        else:
            self.set_emotion_state(self.emotion_state)

    def _build_ui(self) -> None:
        self._build_chrome()
        self._build_sidebar()
        self._build_story_area()
        self._build_task_controls()

    def _build_chrome(self) -> None:
        top = QFrame(self)
        top.setGeometry(4, 4, 1352, 54)
        top.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #67dccb, stop:0.35 #4ecdb9, stop:1 #39b79e);"
            f"border: 3px solid {NAVY}; border-right: 5px solid #04141d; border-bottom: 5px solid #04141d;"
            "border-radius: 5px;"
        )
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
        crumb.setStyleSheet(raised_panel_style("#fffaf2", SOFT_LINE, 4, "#c59a70"))
        label(crumb, "⌂  >  功能导航  >  小游戏", (24, 4, 360, 34), 15, 900)

    def _style_top_chrome(self) -> None:
        top = None
        crumb = None
        for child in self.findChildren(QFrame):
            geom = child.geometry()
            if geom == QRect(4, 4, 1352, 54):
                top = child
            elif geom == QRect(272, 64, 1078, 44):
                crumb = child

        if top is not None:
            header_cover = QFrame(top)
            header_cover.setGeometry(8, 6, 420, 40)
            header_cover.setStyleSheet(
                "QFrame {"
                "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #67dccb, stop:0.35 #4ecdb9, stop:1 #39b79e);"
                "border: none;"
                "}"
            )
            brand_shell = QFrame(header_cover)
            brand_shell.setGeometry(4, 4, 28, 28)
            brand_shell.setStyleSheet(
                "QFrame {"
                "background: rgba(255, 255, 255, 0.16);"
                "border: 2px solid #f7fffd;"
                "border-right: 3px solid #0c5f59;"
                "border-bottom: 3px solid #0c5f59;"
                "border-radius: 6px;"
                "}"
            )
            brand_icon = QLabel(brand_shell)
            brand_icon.setGeometry(3, 3, 20, 20)
            brand_icon.setAlignment(Qt.AlignCenter)
            apply_label_icon(brand_icon, "sidebar_default", 20, "#ffffff")
            label(header_cover, "MoodPet 陪伴中", (38, 2, 260, 32), 16, 900).setStyleSheet(
                "color: white; border: none; background: transparent;"
            )

        if crumb is not None:
            crumb_cover = QFrame(crumb)
            crumb_cover.setGeometry(2, 2, 1074, 40)
            crumb_cover.setStyleSheet(
                "QFrame {"
                "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #fffef8, stop:1 #f7ecda);"
                "border: none;"
                "}"
            )
            crumb_icon = QLabel(crumb_cover)
            crumb_icon.setGeometry(16, 8, 20, 20)
            crumb_icon.setAlignment(Qt.AlignCenter)
            apply_label_icon(crumb_icon, "back", 20, "#247fd8")
            label(crumb_cover, "功能导航  >  小游戏", (42, 2, 360, 32), 15, 900)

    def _build_sidebar(self) -> None:
        self.sidebar, self.sidebar_items = build_pet_sidebar(
            self,
            "games",
            self.open_target,
            geometry=(10, 64, 250, 686),
        )
        return

        self.side_shadow = card_shadow(self, 10, 64, 250, 686, 12, "#a07952")
        side = QFrame(self)
        side.setGeometry(10, 64, 250, 686)
        side.setStyleSheet(raised_panel_style("#fff4df", NAVY, 12, "#0d2230"))

        pet_box = QFrame(side)
        pet_box.setGeometry(58, 20, 134, 126)
        pet_box.setStyleSheet(raised_panel_style("#fff6e9", "#7a5d42", 12, "#6a4e35"))

        pet = QLabel(pet_box)
        pet.setGeometry(8, 8, 118, 110)
        movie = QMovie(str(self.base_dir / "pet" / "init" / "stay.gif"))
        movie.setScaledSize(QSize(108, 108))
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
            item.setGeometry(24, 162 + index * 94, 202, 74)
            border = NAVY if "小游戏" in title else LINE
            item.setStyleSheet(
                f"background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #fffef8, stop:0.22 {color}, stop:1 {color});"
                f"color: {INK}; border: 2px solid {border};"
                f"border-left: 1px solid {LIGHT_EDGE}; border-top: 1px solid {LIGHT_EDGE};"
                f"border-right: 4px solid {SHADOW_DEEP}; border-bottom: 4px solid {SHADOW_DEEP};"
                "border-radius: 10px;"
                "font: 900 13pt 'Microsoft YaHei'; padding-left: 18px;"
            )

        footer = QFrame(side)
        footer.setGeometry(0, 636, 250, 50)
        footer.setStyleSheet(
            f"background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0d3a4a, stop:1 {NAVY});"
            "border: none; border-radius: 0;"
            "border-top: 3px solid #0a2431;"
        )
        label(footer, "♥  MoodPet 陪伴中", (20, 9, 170, 30), 11, 900).setStyleSheet(
            "color: #ffd77d; border: none; font: 900 11pt 'Microsoft YaHei';"
        )
        label(footer, "▂▃▆", (196, 9, 44, 30), 13, 900).setStyleSheet(
            "color: #91f18b; border: none; font: 900 13pt 'Microsoft YaHei';"
        )

    def _build_story_area(self) -> None:
        self.header_shadow = card_shadow(self, 282, 118, 1048, 146, 10, "#a9845d")
        self.header_card = QFrame(self)
        self.header_card.setGeometry(282, 118, 1048, 146)
        self.header_card.setStyleSheet(raised_panel_style(PANEL, SOFT_LINE, 10, "#b48b62"))
        self.thumb = QLabel("", self.header_card)
        self.thumb.setGeometry(22, 22, 88, 88)
        self.thumb.setAlignment(Qt.AlignCenter)
        apply_label_icon(self.thumb, "story_stamp", 48, BLUE_STAMP)
        self.thumb.setStyleSheet(
            f"background-color: {BLUE_STAMP_LIGHT}; color: #ffd28d; border: 3px solid #204c94;"
            "border-left: 1px solid #f7fbff; border-top: 1px solid #f7fbff;"
            "border-right: 4px solid #183c76; border-bottom: 4px solid #183c76;"
            "border-radius: 8px; font: 900 24pt 'Microsoft YaHei';"
        )
        self.story_title = single_line_label(self.header_card, "", (138, 16, 674, 30), 14, 900)
        self.subtitle = single_line_label(self.header_card, "", (140, 52, 672, 24), 10, 700)
        self.progress_label = single_line_label(self.header_card, "", (140, 92, 88, 24), 10, 800)
        self.progress_nodes = single_line_label(self.header_card, "① 开场 ━ ② 事件 ━ ③ 选择 ━ ④ 线索 ━ ⑤ 行动 ━ ⑥ 结尾", (236, 91, 592, 26), 10, 900)
        self.continue_button = PixelButton("继续故事", self.header_card, BLUE, "white")
        self.continue_button.setGeometry(842, 28, 156, 48)
        apply_button_icon(self.continue_button, "story_choice", 24)
        self.continue_button.clicked.connect(self._continue_story)

        self.scene_shadow = card_shadow(self, 282, 276, 640, 430, 10, "#a9845d")
        self.scene = PostalScene(self)
        self.scene.setGeometry(282, 276, 640, 430)

        self.event_shadow = card_shadow(self, 942, 276, 388, 430, 10, "#a9845d")
        self.event_panel = QFrame(self)
        self.event_panel.setGeometry(942, 276, 388, 430)
        self.event_panel.setStyleSheet(raised_panel_style(PANEL, SOFT_LINE, 10, "#b48b62"))
        self.node_title = label(self.event_panel, "", (24, 18, 310, 32), 12, 900)
        self.node_prompt = label(self.event_panel, "", (24, 58, 330, 78), 11, 700)
        for index in range(3):
            button = PixelButton("", self.event_panel, "#fffaf2")
            button.setGeometry(26, 156 + index * 70, 336, 54)
            button.setIconSize(QSize(42, 42))
            self.choice_buttons.append(button)

    def _build_right_panel(self) -> None:
        self.theme_shadow = card_shadow(self, 1040, 118, 292, 132, 10, "#9f7a55")
        self.theme_card = self._right_card(1040, 118, 292, 132, "当前故事主题")
        self.theme_subject = label(self.theme_card, "", (24, 38, 252, 24), 9, 800)
        self.theme_mood = label(self.theme_card, "", (24, 66, 252, 24), 9, 800)
        self.theme_style = label(self.theme_card, "", (24, 94, 252, 24), 9, 800)

        self.feedback_shadow = card_shadow(self, 1040, 266, 292, 116, 10, "#9f7a55")
        self.feedback_card = self._right_card(1040, 266, 292, 116, "桌宠反馈")
        mascot = QLabel(self.feedback_card)
        mascot.setGeometry(18, 34, 72, 66)
        movie = QMovie(str(self.base_dir / "pet" / "init" / "stay.gif"))
        movie.setScaledSize(QSize(70, 70))
        mascot.setMovie(movie)
        movie.start()
        self.feedback_pet_movie = movie
        self.feedback = label(self.feedback_card, "", (100, 40, 170, 54), 11, 900)

        self.links_shadow = card_shadow(self, 1040, 398, 292, 116, 10, "#9f7a55")
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

        self.rewards_shadow = card_shadow(self, 1040, 530, 292, 132, 10, "#9f7a55")
        rewards = self._right_card(1040, 530, 292, 132, "本次故事收获")
        for index in range(4):
            row = label(rewards, "", (24, 38 + index * 24, 230, 22), 9, 800)
            self.reward_rows.append(row)

        self.restart_button = PixelButton("重新开始", self, MINT, "white")
        self.restart_button.setGeometry(1048, 672, 274, 42)
        apply_button_icon(self.restart_button, "restart", 24)
        self.restart_button.clicked.connect(self._restart)
        self.back_button = PixelButton("返回导航", self, BLUE, "white")
        self.back_button.setGeometry(1048, 716, 274, 32)
        apply_button_icon(self.back_button, "back", 24)
        self.back_button.clicked.connect(self.hide)

    def _build_task_controls(self) -> None:
        self.task_panel = QFrame(self.event_panel)
        self.task_panel.setGeometry(24, 328, 340, 88)
        self.task_panel.setStyleSheet(raised_panel_style(PANEL, SOFT_LINE, 8, "#b48b62"))

        self.task_status = label(self.task_panel, "", (14, 6, 180, 24), 10, 800)
        self.inline_continue_button = PixelButton("继续", self.task_panel, BLUE, "white")
        self.inline_continue_button.setGeometry(14, 38, 96, 38)
        apply_button_icon(self.inline_continue_button, "story_choice", 18)
        self.inline_continue_button.clicked.connect(self._continue_story)

        self.restart_button = PixelButton("重新开始", self.task_panel, MINT, "white")
        self.restart_button.setGeometry(120, 38, 106, 38)
        apply_button_icon(self.restart_button, "restart", 18)
        self.restart_button.clicked.connect(self._restart)

        self.back_button = PixelButton("返回", self.task_panel, BLUE, "white")
        self.back_button.setGeometry(236, 38, 88, 38)
        apply_button_icon(self.back_button, "back", 18)
        self.back_button.clicked.connect(self.hide)

    def _right_card(self, x: int, y: int, w: int, h: int, title: str) -> QFrame:
        card = QFrame(self)
        card.setGeometry(x, y, w, h)
        card.setStyleSheet(raised_panel_style(PANEL, SOFT_LINE, 10, "#b48b62"))
        label(card, title, (20, 8, w - 40, 26), 11, 900)
        return card

    def refresh(self) -> None:
        node = current_node(self.state)
        self.story_title.setText(f"本次故事： {self.state.story_title}")
        self.subtitle.setText(self.state.subtitle)
        self.progress_label.setText(progress_text(self.state))
        self.scene.set_caption(node.scene_text)
        self._prefetch_node_image()
        self._refresh_header_image()
        self.node_title.setText(node.title)
        self.node_prompt.setText(node.prompt)
        if hasattr(self, "feedback"):
            self.feedback.setText(node.pet_reply)
        if hasattr(self, "task_status"):
            if self.state.node_index >= len(self.state.nodes) - 1:
                self.task_status.setText("故事已完成")
            elif self.state.interaction_done:
                self.task_status.setText("剧情推进中")
            else:
                self.task_status.setText("请选择行动")

        choices = available_choices(self.state)
        for index, button in enumerate(self.choice_buttons):
            if index < len(choices):
                choice = choices[index]
                available = max(0, button.width() - 46)
                button.setText(button.fontMetrics().elidedText(choice.title, Qt.ElideRight, available))
                self._apply_choice_button_image(button, choice.id)
                button.show()
                try:
                    button.clicked.disconnect()
                except TypeError:
                    pass
                button.clicked.connect(lambda checked=False, choice_id=choice.id: self._choose(choice_id))
            else:
                button.setIcon(QIcon())
                button.hide()
        self._prefetch_choice_images(choices)

        if hasattr(self, "clue_title"):
            self.clue_title.setText(f"🔎 已收集线索        {collected_count_text(self.state)}")
        if hasattr(self, "theme_subject"):
            self.theme_subject.setText(f"✉ 主题：   {self.state.theme_subject}")
            self.theme_mood.setText(f"♧ 氛围：   {self.state.theme_mood}")
            self.theme_style.setText(f"★ 风格：   {self.state.theme_style}")
        if hasattr(self, "reward_rows") and self.reward_rows:
            for index, reward in enumerate(self.state.rewards):
                self.reward_rows[index].setText(f"{reward.icon}  {reward.label:<8} +{reward.value}")
            self.reward_rows[3].setText(f"▤  线索记录       {collected_count_text(self.state)}")
        if hasattr(self, "envelope"):
            self.envelope.setVisible(not self.state.interaction_done)
            if not self.state.interaction_done:
                self.envelope.reset_position()
                self.interaction_tip.setText("提示：将信纸拖到信封里")
            else:
                self.interaction_tip.setText("已归位：信纸安静地躺在信封里")

    def _choose(self, choice_id: str) -> None:
        image_key = self._choice_image_key(self.state, choice_id)
        with self._image_lock:
            self.selected_choice_image_key = image_key
            self.selected_choice_image_path = self.choice_image_paths.get(image_key)
        self.state = choose_event(self.state, choice_id)
        self.refresh()

    def _complete_interaction(self) -> None:
        self.state = complete_interaction(self.state)
        self.refresh()

    def _continue_story(self) -> None:
        if self.state.interaction_done and self.state.node_index < len(self.state.nodes) - 1:
            self.state = continue_story(self.state)
        elif not self.state.interaction_done:
            self._set_feedback("先选择一个行动，故事会沿着这条线索继续。")
        self.refresh()

    def _restart(self) -> None:
        self.state = restart_game(self.state)
        self.selected_choice_image_key = ""
        self.selected_choice_image_path = None
        self.refresh()

    def _set_feedback(self, text: str) -> None:
        if hasattr(self, "feedback"):
            self.feedback.setText(text)

    def _prefetch_choice_images(self, choices) -> None:
        if self.choice_image_service is None:
            return
        for choice in choices:
            self._queue_choice_image(self.state, choice)

    def _generate_choice_image(self, state: MiniGameState, choice) -> None:
        try:
            assert self.choice_image_service is not None
            path = self.choice_image_service.ensure_choice_image(state, choice)
            image_key = self._choice_image_key(state, choice.id)
            with self._image_lock:
                self.choice_image_paths[image_key] = path
                self.choice_image_errors.pop(image_key, None)
        except Exception as exc:
            image_key = self._choice_image_key(state, choice.id)
            with self._image_lock:
                self.choice_image_errors[image_key] = str(exc)
        finally:
            image_key = self._choice_image_key(state, choice.id)
            with self._image_lock:
                self.choice_image_loading.discard(image_key)

    def _refresh_choice_images(self) -> None:
        choices = available_choices(self.state)
        for index, choice in enumerate(choices[: len(self.choice_buttons)]):
            self._apply_choice_button_image(self.choice_buttons[index], choice.id)
        self._refresh_header_image()

    def _prefetch_node_image(self) -> None:
        if self.choice_image_service is None:
            return
        self._queue_node_image(self.state)

    def _generate_node_image(self, state: MiniGameState) -> None:
        image_key = self._node_image_key(state)
        try:
            assert self.choice_image_service is not None
            path = self.choice_image_service.ensure_node_image(state)
            with self._image_lock:
                self.node_image_paths[image_key] = path
                self.node_image_errors.pop(image_key, None)
        except Exception as exc:
            with self._image_lock:
                self.node_image_errors[image_key] = str(exc)
        finally:
            with self._image_lock:
                self.node_image_loading.discard(image_key)

    def _apply_choice_button_image(self, button: PixelButton, choice_id: str) -> None:
        image_key = self._choice_image_key(self.state, choice_id)
        with self._image_lock:
            path = self.choice_image_paths.get(image_key)
            loading = image_key in self.choice_image_loading
        if path and path.exists():
            pixmap = QPixmap(str(path))
            if not pixmap.isNull():
                button.setIcon(QIcon(pixmap.scaled(28, 28, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)))
                return
        if loading:
            button.setIcon(QIcon(render_placeholder_pixmap(28)))
        else:
            apply_button_icon(button, "story_choice", 24)

    def _prime_story_assets(self) -> None:
        if self.choice_image_service is None or self.story_assets_primed:
            return
        self.story_assets_primed = True
        for state in build_story_render_states(self.state):
            self._queue_node_image(state)
        for choice in self.state.choices:
            self._queue_choice_image(self.state, choice)

    def _queue_choice_image(self, state: MiniGameState, choice) -> None:
        with self._image_lock:
            image_key = self._choice_image_key(state, choice.id)
            if image_key in self.choice_image_paths or image_key in self.choice_image_loading:
                return
            self.choice_image_loading.add(image_key)
        thread = threading.Thread(
            target=self._generate_choice_image,
            args=(state, choice),
            name=f"MoodPetSeedream-{choice.id}-{state.node_index}",
            daemon=True,
        )
        thread.start()

    def _queue_node_image(self, state: MiniGameState) -> None:
        with self._image_lock:
            image_key = self._node_image_key(state)
            if image_key in self.node_image_paths or image_key in self.node_image_loading:
                return
            self.node_image_loading.add(image_key)
        thread = threading.Thread(
            target=self._generate_node_image,
            args=(state,),
            name=f"MoodPetSeedreamNode-{current_node(state).id}-{state.node_index}",
            daemon=True,
        )
        thread.start()

    def _choice_image_key(self, state: MiniGameState, choice_id: str) -> str:
        return f"{state.node_index}:{choice_id}"

    def _node_image_key(self, state: MiniGameState) -> str:
        return f"node:{state.node_index}:{current_node(state).id}"

    def _refresh_header_image(self) -> None:
        with self._image_lock:
            selected_path = self.choice_image_paths.get(self.selected_choice_image_key, self.selected_choice_image_path)
            node_path = self.node_image_paths.get(self._node_image_key(self.state))
        path = node_path or selected_path or self._first_available_choice_image_path()
        if path and path.exists():
            pixmap = QPixmap(str(path))
            if not pixmap.isNull():
                self.thumb.setPixmap(pixmap.scaled(88, 88, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
                self.scene.set_image_path(path)
                return
        self.thumb.setPixmap(QPixmap())
        self.scene.set_image_path(None)
        apply_label_icon(self.thumb, "story_stamp", 48, BLUE_STAMP)

    def _first_available_choice_image_path(self) -> Optional[Path]:
        for choice in available_choices(self.state):
            image_key = self._choice_image_key(self.state, choice.id)
            with self._image_lock:
                path = self.choice_image_paths.get(image_key)
            if path and path.exists():
                return path
        return None

    def set_emotion_state(self, emotion_state: EmotionState) -> None:
        self.emotion_state = emotion_state
        self.story_assets_primed = False
        self.selected_choice_image_key = ""
        self.selected_choice_image_path = None
        if self.generate_story:
            self._start_story_generation()
        else:
            self.initial_story_state = self.story_generation_service.build_local_story(emotion_state)
            self.state = self.initial_story_state
            self.story_loading = False
            self.refresh()
            if self.preload_story_assets:
                self._prime_story_assets()

    def refresh(self) -> None:
        if self.story_loading:
            self._render_story_loading()
            return
        node = current_node(self.state)
        set_elided_label_text(self.story_title, f"本次故事：{self.state.story_title}")
        subtitle_text = self.state.subtitle
        if self.state.emotion_summary:
            subtitle_text = f"{subtitle_text} · {self.state.emotion_summary}"
        set_elided_label_text(self.subtitle, subtitle_text)
        self.progress_label.setText(progress_text(self.state))
        self.scene.set_caption(node.scene_text)
        self._prefetch_node_image()
        self._refresh_header_image()
        self.node_title.setText(node.title)
        self.node_prompt.setText(node.prompt)
        if hasattr(self, "feedback"):
            self.feedback.setText(node.pet_reply)
        if hasattr(self, "task_status"):
            if self.state.node_index >= len(self.state.nodes) - 1:
                self.task_status.setText("故事已完成")
            elif self.state.interaction_done:
                self.task_status.setText("剧情推进中")
            else:
                self.task_status.setText("请选择行动")

        choices = available_choices(self.state)
        for index, button in enumerate(self.choice_buttons):
            if index < len(choices):
                choice = choices[index]
                available = max(0, button.width() - 46)
                button.setText(button.fontMetrics().elidedText(choice.title, Qt.ElideRight, available))
                self._apply_choice_button_image(button, choice.id)
                button.show()
                try:
                    button.clicked.disconnect()
                except TypeError:
                    pass
                button.clicked.connect(lambda checked=False, choice_id=choice.id: self._choose(choice_id))
            else:
                button.setIcon(QIcon())
                button.hide()
        self._prefetch_choice_images(choices)

        if hasattr(self, "clue_title"):
            self.clue_title.setText(f"已收集线索       {collected_count_text(self.state)}")
        if hasattr(self, "theme_subject"):
            self.theme_subject.setText(f"主题：  {self.state.theme_subject}")
            self.theme_mood.setText(f"氛围：  {self.state.theme_mood}")
            self.theme_style.setText(f"风格：  {self.state.theme_style}")
        if hasattr(self, "reward_rows") and self.reward_rows:
            for index, reward in enumerate(self.state.rewards):
                self.reward_rows[index].setText(f"{reward.icon}  {reward.label:<8} +{reward.value}")
            self.reward_rows[3].setText(f"线索记录       {collected_count_text(self.state)}")
        if hasattr(self, "envelope"):
            self.envelope.setVisible(not self.state.interaction_done)
            if not self.state.interaction_done:
                self.envelope.reset_position()
                self.interaction_tip.setText("提示：将信纸拖到信封里")
            else:
                self.interaction_tip.setText("已归位：信纸安静地躺在信封里")

        if hasattr(self, "continue_button"):
            self.continue_button.setEnabled(True)
        if hasattr(self, "inline_continue_button"):
            self.inline_continue_button.setEnabled(True)
        if hasattr(self, "restart_button"):
            self.restart_button.setEnabled(True)

    def _render_story_loading(self) -> None:
        set_elided_label_text(self.story_title, "正在生成剧情")
        set_elided_label_text(self.subtitle, f"{self.emotion_state.label_zh} · {self.emotion_state.message}")
        self.progress_label.setText("剧情准备中")
        self.scene.set_caption("正在根据当前情绪生成更适合你的故事...")
        self.scene.set_image_path(None)
        self.thumb.setPixmap(QPixmap())
        apply_label_icon(self.thumb, "story_stamp", 48, BLUE_STAMP)
        self.node_title.setText("情绪分析中")
        self.node_prompt.setText("故事还在生成，请稍等一下。")
        if hasattr(self, "feedback"):
            self.feedback.setText("先等一会儿，MoodPet 正在把剧情变成更适合你的样子。")
        if hasattr(self, "task_status"):
            self.task_status.setText("剧情生成中，请稍等")
        if hasattr(self, "continue_button"):
            self.continue_button.setEnabled(False)
        if hasattr(self, "inline_continue_button"):
            self.inline_continue_button.setEnabled(False)
        if hasattr(self, "restart_button"):
            self.restart_button.setEnabled(False)
        if hasattr(self, "back_button"):
            self.back_button.setEnabled(True)
        for button in self.choice_buttons:
            button.hide()

    def _start_story_generation(self) -> None:
        self.story_generation_request_id += 1
        request_id = self.story_generation_request_id
        self.story_loading = True
        self.refresh()
        state_snapshot = self.emotion_state
        thread = threading.Thread(
            target=self._generate_story,
            args=(request_id, state_snapshot),
            name=f"MoodPetStory-{state_snapshot.emotion}-{request_id}",
            daemon=True,
        )
        thread.start()

    def _generate_story(self, request_id: int, emotion_state: EmotionState) -> None:
        try:
            state = self.story_generation_service.generate(emotion_state)
            self.story_generation_queue.put((request_id, True, state))
        except Exception as exc:
            self.story_generation_queue.put((request_id, False, str(exc)))

    def _poll_story_generation_result(self) -> None:
        try:
            while True:
                request_id, ok, payload = self.story_generation_queue.get_nowait()
                if request_id != self.story_generation_request_id:
                    continue
                if ok and isinstance(payload, MiniGameState):
                    self.initial_story_state = payload
                    self.state = payload
                else:
                    self.initial_story_state = self.story_generation_service.build_local_story(self.emotion_state)
                    self.state = self.initial_story_state
                self.story_loading = False
                self.story_assets_primed = False
                self.selected_choice_image_key = ""
                self.selected_choice_image_path = None
                self.refresh()
                if self.preload_story_assets:
                    self._prime_story_assets()
        except queue.Empty:
            pass

    def _prefetch_choice_images(self, choices) -> None:
        if self.story_loading or self.choice_image_service is None:
            return
        for choice in choices:
            self._queue_choice_image(self.state, choice)

    def _prefetch_node_image(self) -> None:
        if self.story_loading or self.choice_image_service is None:
            return
        self._queue_node_image(self.state)

    def _refresh_choice_images(self) -> None:
        if self.story_loading:
            return
        choices = available_choices(self.state)
        for index, choice in enumerate(choices[: len(self.choice_buttons)]):
            self._apply_choice_button_image(self.choice_buttons[index], choice.id)
        self._refresh_header_image()

    def _restart(self) -> None:
        self.state = self.initial_story_state
        self.selected_choice_image_key = ""
        self.selected_choice_image_path = None
        self.story_assets_primed = False
        self.refresh()
        if self.preload_story_assets:
            self._prime_story_assets()

    def _continue_story(self) -> None:
        if self.story_loading:
            return
        if self.state.interaction_done and self.state.node_index < len(self.state.nodes) - 1:
            self.state = continue_story(self.state)
        elif not self.state.interaction_done:
            self._set_feedback("先选择一个行动，故事会沿着这条线索继续。")
        self.refresh()
