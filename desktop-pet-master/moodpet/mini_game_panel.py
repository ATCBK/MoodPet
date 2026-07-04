from pathlib import Path
from typing import List, Optional, Tuple

from PyQt5.QtCore import QPoint, QRect, QSize, Qt
from PyQt5.QtGui import QColor, QFont, QMovie, QPainter, QPainterPath, QPen, QPixmap
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
    def __init__(self, base_dir: Path, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.base_dir = base_dir
        self.state = build_default_game()
        self.choice_buttons: List[PixelButton] = []
        self.clue_cards: List[QFrame] = []
        self.clue_card_icons: List[QLabel] = []
        self.clue_card_titles: List[QLabel] = []
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

    def _build_sidebar(self) -> None:
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
        self.header_shadow = card_shadow(self, 282, 118, 740, 146, 10, "#a9845d")
        self.header_card = QFrame(self)
        self.header_card.setGeometry(282, 118, 740, 146)
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
        self.story_title = label(self.header_card, "", (138, 14, 410, 34), 14, 900)
        self.subtitle = label(self.header_card, "", (140, 50, 390, 28), 10, 700)
        self.progress_label = label(self.header_card, "", (140, 84, 100, 24), 10, 800)
        self.progress_nodes = label(self.header_card, "① 开场 ━ ② 事件 ━ ③ 选择 ━ ④ 线索 ━ ⑤ 结尾", (250, 82, 430, 28), 10, 900)
        self.continue_button = PixelButton("继续故事", self.header_card, BLUE, "white")
        self.continue_button.setGeometry(536, 28, 156, 48)
        apply_button_icon(self.continue_button, "story_choice", 24)
        self.continue_button.clicked.connect(self._continue_story)

        self.scene_shadow = card_shadow(self, 282, 276, 374, 306, 10, "#a9845d")
        self.scene = PostalScene(self)
        self.scene.setGeometry(282, 276, 374, 306)

        self.event_shadow = card_shadow(self, 668, 276, 354, 236, 10, "#a9845d")
        self.event_panel = QFrame(self)
        self.event_panel.setGeometry(668, 276, 354, 236)
        self.event_panel.setStyleSheet(raised_panel_style(PANEL, SOFT_LINE, 10, "#b48b62"))
        self.node_title = label(self.event_panel, "", (22, 12, 250, 28), 11, 900)
        self.node_prompt = label(self.event_panel, "", (22, 40, 310, 54), 10, 700)
        for index in range(3):
            button = PixelButton("", self.event_panel, "#fffaf2")
            button.setGeometry(28, 98 + index * 42, 298, 34)
            self.choice_buttons.append(button)

        self.clue_shadow = card_shadow(self, 282, 596, 300, 126, 10, "#a9845d")
        self.clue_panel = QFrame(self)
        self.clue_panel.setGeometry(282, 596, 300, 126)
        self.clue_panel.setStyleSheet(raised_panel_style(PANEL, SOFT_LINE, 10, "#b48b62"))
        self.clue_title = label(self.clue_panel, "", (18, 8, 180, 28), 11, 900)
        self.clue_cards = []
        self.clue_card_icons: List[QLabel] = []
        self.clue_card_titles: List[QLabel] = []
        for index in range(3):
            x = 18 + index * 92
            shadow = QFrame(self.clue_panel)
            shadow.setGeometry(x + 4, 46 + 4, 84, 66)
            shadow.setStyleSheet("background-color: #c19b6f; border: none; border-radius: 8px;")
            card = QFrame(self.clue_panel)
            card.setGeometry(x, 46, 84, 66)
            card.setStyleSheet(raised_panel_style("#fff4e0", "#c69969", 8, "#a97951"))
            icon = QLabel(card)
            icon.setGeometry(12, 4, 60, 30)
            icon.setAlignment(Qt.AlignCenter)
            icon.setStyleSheet("background: transparent; border: none;")
            title = QLabel(card)
            title.setGeometry(6, 36, 72, 22)
            title.setAlignment(Qt.AlignCenter)
            title.setWordWrap(True)
            title.setStyleSheet(
                "background: transparent; border: none; color: #10151b;"
                "font: 900 9pt 'Microsoft YaHei';"
            )
            self.clue_cards.append(card)
            self.clue_card_icons.append(icon)
            self.clue_card_titles.append(title)

        self.interaction_shadow = card_shadow(self, 594, 596, 296, 126, 10, "#a9845d")
        self.interaction_panel = QFrame(self)
        self.interaction_panel.setGeometry(594, 596, 296, 126)
        self.interaction_panel.setStyleSheet(raised_panel_style(PANEL, SOFT_LINE, 10, "#b48b62"))
        label(self.interaction_panel, "☝ 轻量互动", (18, 7, 154, 28), 12, 800)
        label(self.interaction_panel, "整理散落信笺（拖拽归位）", (18, 32, 230, 24), 10, 700)
        self.interaction_stack = QLabel(self.interaction_panel)
        self.interaction_stack.setGeometry(14, 48, 82, 56)
        self.interaction_stack.setAlignment(Qt.AlignCenter)
        self.interaction_stack.setStyleSheet("background: transparent; border: none;")
        self.interaction_stack.setPixmap(render_paper_stack_pixmap(76))
        self.interaction_arrow = QLabel("›", self.interaction_panel)
        self.interaction_arrow.setGeometry(104, 56, 18, 24)
        self.interaction_arrow.setAlignment(Qt.AlignCenter)
        self.interaction_arrow.setStyleSheet(
            "background: transparent; border: none; color: #8b6a4d; font: 900 18pt 'Microsoft YaHei';"
        )
        self.drop_target = QLabel("", self.interaction_panel)
        self.drop_target.setGeometry(176, 48, 96, 56)
        self.drop_target.setAlignment(Qt.AlignCenter)
        self.drop_target.setStyleSheet(
            "background: transparent; color: #9a7256; border: 2px dashed #b99169;"
            "border-left: 1px solid #f7fbff; border-top: 1px solid #f7fbff;"
            "border-right: 4px solid #ab835a; border-bottom: 4px solid #ab835a;"
            "border-radius: 6px; font: 900 10pt 'Microsoft YaHei';"
        )
        self.drop_target_icon = QLabel(self.drop_target)
        self.drop_target_icon.setGeometry(12, 4, 72, 46)
        self.drop_target_icon.setAlignment(Qt.AlignCenter)
        self.drop_target_icon.setStyleSheet("background: transparent; border: none;")
        self.drop_target_icon.setPixmap(render_envelope_pixmap(72))
        self.drop_target_caption = QLabel("信封", self.drop_target)
        self.drop_target_caption.setGeometry(0, 38, 96, 16)
        self.drop_target_caption.setAlignment(Qt.AlignCenter)
        self.drop_target_caption.setStyleSheet(
            "background: transparent; border: none; color: #9a7256; font: 900 9pt 'Microsoft YaHei';"
        )
        self.envelope = DraggableEnvelope(self.interaction_panel, self.drop_target.geometry(), self._complete_interaction)
        self.interaction_tip = label(self.interaction_panel, "提示：把信纸拖到信封里", (84, 95, 194, 24), 9, 700)

        self.pet_note = QLabel(self)
        self.pet_note.setGeometry(882, 582, 130, 78)
        self.pet_note.setWordWrap(True)
        self.pet_note.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.pet_note.setStyleSheet(
            f"background-color: {PANEL}; color: {INK}; border: 2px solid {LINE};"
            "border-left: 1px solid #fffef8; border-top: 1px solid #fffef8;"
            "border-right: 4px solid #b58a61; border-bottom: 4px solid #b58a61;"
            "border-radius: 8px;"
            "font-family: 'Microsoft YaHei'; font-size: 9pt; font-weight: 900; padding: 8px;"
        )
        pet = QLabel(self)
        pet.setGeometry(936, 658, 92, 72)
        note_movie = QMovie(str(self.base_dir / "pet" / "init" / "stay.gif"))
        note_movie.setScaledSize(QSize(82, 82))
        pet.setMovie(note_movie)
        note_movie.start()
        self.note_pet_movie = note_movie

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
        self.node_title.setText(node.title)
        self.node_prompt.setText(node.prompt)
        self.pet_note.setText(node.pet_reply)
        self.feedback.setText(node.pet_reply)

        choices = available_choices(self.state)
        for index, button in enumerate(self.choice_buttons):
            if index < len(choices):
                choice = choices[index]
                available = max(0, button.width() - 46)
                button.setText(button.fontMetrics().elidedText(choice.title, Qt.ElideRight, available))
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
                icon_feature, icon_color, fill_color = CLUE_ICON_MAP.get(
                    clue.id,
                    ("note", "#7f6a57", "#fff2e4"),
                )
                if icon_feature == "story_stamp":
                    self.clue_card_icons[index].setPixmap(render_stamp_pixmap(44))
                elif icon_feature == "story_clock":
                    self.clue_card_icons[index].setPixmap(render_clock_pixmap(44))
                elif icon_feature == "note":
                    self.clue_card_icons[index].setPixmap(render_placeholder_pixmap(44))
                else:
                    apply_label_icon(self.clue_card_icons[index], icon_feature, 24, icon_color)
                self.clue_card_titles[index].setText(clue.title)
                card.setStyleSheet(raised_panel_style(fill_color, "#c89969", 8, "#a67a51"))
                self.clue_card_icons[index].show()
                self.clue_card_titles[index].show()
            else:
                self.clue_card_icons[index].setPixmap(render_placeholder_pixmap(44))
                self.clue_card_titles[index].setText("等待发现")
                self.clue_card_titles[index].show()
                card.setStyleSheet(
                    "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #fffdf7, stop:1 #f5e8d7);"
                    "border: 2px dashed #c7a989;"
                    "border-left: 1px solid #fffef8; border-top: 1px solid #fffef8;"
                    "border-right: 4px solid #b99067; border-bottom: 4px solid #b99067;"
                    "border-radius: 8px;"
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
