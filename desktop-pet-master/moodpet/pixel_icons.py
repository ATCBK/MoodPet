from pathlib import Path
from typing import Dict

from PyQt5.QtCore import QByteArray, QSize, Qt
from PyQt5.QtGui import QIcon, QPainter, QPixmap
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWidgets import QLabel, QPushButton


BASE_DIR = Path(__file__).resolve().parents[1]
ICON_ASSETS_DIR = BASE_DIR / "assets" / "icons" / "pixelarticons"
DEFAULT_ICON_COLOR = "#071927"

MOODPET_ICONS: Dict[str, str] = {
    "pet": "pixelarticons:heart",
    "navigation": "pixelarticons:grid",
    "realtime": "pixelarticons:camera",
    "todo": "pixelarticons:checklist",
    "games": "pixelarticons:gamepad",
    "settings": "pixelarticons:sliders",
    "bubble": "pixelarticons:message",
    "message": "pixelarticons:message",
    "camera": "pixelarticons:camera",
    "video": "pixelarticons:video",
    "voice": "pixelarticons:mic",
    "privacy": "pixelarticons:lock",
    "power": "pixelarticons:power",
    "restart": "pixelarticons:reload",
    "back": "pixelarticons:home",
    "close": "pixelarticons:close",
    "story_clue": "pixelarticons:book",
    "story_choice": "pixelarticons:message-text",
    "companion": "pixelarticons:heart",
    "note": "pixelarticons:note",
    "list": "pixelarticons:list",
    "alert": "pixelarticons:bell",
}


def pixel_icon_name(feature: str) -> str:
    try:
        return MOODPET_ICONS[feature]
    except KeyError as exc:
        raise KeyError(f"Unknown MoodPet icon feature: {feature}") from exc


def icon_asset_path(feature: str) -> Path:
    icon_name = pixel_icon_name(feature)
    icon_id = icon_name.split(":", 1)[1]
    return ICON_ASSETS_DIR / f"{icon_id}.svg"


def qicon(feature: str, color: str = DEFAULT_ICON_COLOR, size: int = 24) -> QIcon:
    svg = icon_asset_path(feature).read_text(encoding="utf-8").replace("currentColor", color)
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    icon = QIcon()
    icon.addPixmap(pixmap)
    return icon


def apply_button_icon(button: QPushButton, feature: str, size: int = 24, color: str = DEFAULT_ICON_COLOR) -> QPushButton:
    button.setIcon(qicon(feature, color, size))
    button.setIconSize(QSize(size, size))
    return button


def apply_label_icon(label: QLabel, feature: str, size: int = 24, color: str = DEFAULT_ICON_COLOR) -> QLabel:
    label.setPixmap(qicon(feature, color, size).pixmap(size, size))
    return label
