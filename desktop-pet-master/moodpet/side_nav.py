from typing import Callable, List, Optional, Tuple

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QLabel, QWidget

from moodpet.pixel_icons import apply_label_icon


NAVY = "#062b36"
TEAL = "#2fe6bd"
ACTIVE = "#20b987"
ACTIVE_EDGE = "#a8ffce"
ITEM_BG = "rgba(11, 58, 70, 160)"
WHITE = "#f7fffd"
GOLD = "#ffd77d"


class SidebarNavLabel(QLabel):
    def __init__(self, text: str, parent: QWidget, on_click: Callable[[str], None], module_id: str) -> None:
        super().__init__(text, parent)
        self._on_click = on_click
        self._module_id = module_id
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._on_click(self._module_id)
            event.accept()
            return
        super().mousePressEvent(event)


def build_pet_sidebar(
    parent: QWidget,
    active_module: str,
    open_target: Optional[Callable[[str], None]] = None,
    geometry: Tuple[int, int, int, int] = (12, 12, 260, 736),
) -> Tuple[QFrame, List[Tuple[QFrame, QLabel, QLabel]]]:
    on_click = open_target or (lambda module_id: None)
    sidebar = QFrame(parent)
    sidebar.setObjectName("petSidebar")
    sidebar.setGeometry(*geometry)
    sidebar.setStyleSheet(
        "QFrame#petSidebar {"
        f"background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #083842, stop:1 {NAVY});"
        f"border: 3px solid {TEAL};"
        "border-radius: 8px;"
        "}"
    )

    brand_shell = QFrame(sidebar)
    brand_shell.setGeometry(14, 14, 232, 76)
    brand_shell.setStyleSheet(
        "QFrame {"
        "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0b3943, stop:0.45 #092d38, stop:1 #071d28);"
        "border: 3px solid #23e1ca;"
        "border-right: 5px solid #041821;"
        "border-bottom: 5px solid #041821;"
        "border-radius: 14px;"
        "}"
    )

    brand_title = QFrame(sidebar)
    brand_title.setGeometry(28, 22, 206, 40)
    brand_title.setStyleSheet("background: transparent; border: none;")
    brand = QLabel("MoodPet", brand_title)
    brand.setGeometry(0, 0, 164, 40)
    brand.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    brand.setStyleSheet("color: white; border: none; background: transparent; font-family: 'Microsoft YaHei'; font-size: 21pt; font-weight: 900;")

    brand_paw = QLabel("", brand_title)
    brand_paw.setGeometry(172, 6, 24, 24)
    brand_paw.setAlignment(Qt.AlignCenter)
    brand_paw.setStyleSheet("background: transparent; border: none;")
    apply_label_icon(brand_paw, "sidebar_paw", 24, "#ffcf6a")

    dash = QLabel("", sidebar)
    dash.setGeometry(28, 80, 216, 2)
    dash.setStyleSheet("background-color: rgba(47, 230, 189, 220); border: none;")

    items = [
        ("sidebar_default", "桌宠默认态", "default"),
        ("sidebar_realtime", "实时检测", "realtime"),
        ("sidebar_todo", "待办", "todo"),
        ("sidebar_games", "小游戏", "games"),
        ("sidebar_settings", "设置", "settings"),
    ]
    sidebar_items: List[Tuple[QFrame, QLabel, QLabel]] = []
    for index, (icon, text, module_id) in enumerate(items):
        item = QFrame(sidebar)
        item.setGeometry(24, 112 + index * 62, 214, 46)
        is_active = module_id == active_module
        if is_active:
            item.setStyleSheet(
                "QFrame {"
                f"background-color: {ACTIVE};"
                f"border: 2px dashed {ACTIVE_EDGE};"
                "border-radius: 8px;"
                "}"
            )
        else:
            item.setStyleSheet(
                "QFrame {"
                f"background-color: {ITEM_BG};"
                "border: none;"
                "border-radius: 8px;"
                "}"
            )

        icon_label = QLabel("", item)
        icon_label.setGeometry(14, 8, 30, 30)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("background: transparent; border: none;")
        apply_label_icon(icon_label, icon, 28, WHITE)

        text_label = SidebarNavLabel(text, item, on_click, module_id)
        text_label.setGeometry(54, 0, 152, 46)
        text_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        text_label.setStyleSheet("color: white; border: none; background: transparent; font-family: 'Microsoft YaHei'; font-size: 14pt; font-weight: 800;")

        item.setCursor(Qt.PointingHandCursor)
        icon_label.setCursor(Qt.PointingHandCursor)
        item.mousePressEvent = lambda event, selected_module_id=module_id: _open_sidebar_target(event, on_click, selected_module_id)
        icon_label.mousePressEvent = lambda event, selected_module_id=module_id: _open_sidebar_target(event, on_click, selected_module_id)
        sidebar_items.append((item, icon_label, text_label))

    footer = QLabel("♥ MoodPet 陪伴中          ▂▄▆█", sidebar)
    footer.setGeometry(22, geometry[3] - 48, 216, 24)
    footer.setStyleSheet("color: #ffd77d; border: none; background: transparent; font-family: 'Microsoft YaHei'; font-size: 11pt; font-weight: 800;")
    return sidebar, sidebar_items


def _open_sidebar_target(event, open_target: Callable[[str], None], module_id: str) -> None:
    if event.button() == Qt.LeftButton:
        open_target(module_id)
        event.accept()
