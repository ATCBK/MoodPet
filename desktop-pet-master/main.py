import json
import os
import pathlib
import queue
import random
import subprocess
import sys
import time
import webbrowser
from datetime import datetime
from pathlib import Path

from PyQt5.QtCore import QSize, Qt, QTimer
from PyQt5.QtGui import QCursor, QIcon, QMovie
from PyQt5.QtWidgets import QAction, QApplication, QFrame, QLabel, QMainWindow, QMenu, QPushButton, QSystemTrayIcon

from middlewares.self_log import DesktopPetLogger
from moodpet.bubble_policy import BubbleContext, BubbleSettings, build_bubble_reply, can_emit_bubble
from moodpet.emotion import build_emotion_state
from moodpet.emotion_camera import EmotionCameraWorker
from moodpet.mini_game_panel import MiniGamePanelWindow
from moodpet.pixel_icons import apply_button_icon, apply_label_icon
from moodpet.realtime_panel import RealtimeMonitorWindow
from moodpet.settings_panel import SettingsPanelWindow
from moodpet.todo_panel import TodoPanelWindow
from moodpet.ui_state import (
    build_feature_modules,
    build_navigation_groups,
    camera_status_text,
    pet_bubble_text,
    should_open_navigation,
)


BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "models" / "emotion-ferplus-8.onnx"


class DemoWin(QMainWindow):
    def __init__(self):
        super().__init__()
        self._init_logger()
        self.is_follow_mouse = False
        self.drag_started = False
        self.condition = 0
        self.emotion_enabled = False
        self.current_emotion_state = build_emotion_state("disabled")
        self.bubble_settings = BubbleSettings(frequency="medium", do_not_disturb=True)
        self.last_bubble_emit_seconds = None
        self.active_bubble_target_id = "realtime"
        self.emotion_queue: "queue.Queue" = queue.Queue(maxsize=1)
        self.emotion_worker = EmotionCameraWorker(self.emotion_queue, MODEL_PATH)
        self.realtime_monitor = None
        self.mini_game_panel = None
        self.todo_panel = None
        self.settings_panel = None

        self._init_ui()
        self._init_tray()
        self._init_pet_actions()
        self._init_timers()

        self.move(1650, 20)
        self.show_emotion_state(self.current_emotion_state)

    def _init_logger(self):
        timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f-")[:-3]
        filename = timestamp + ".log"
        self.log = DesktopPetLogger(pathlib.Path("./logs"), filename)

    def _init_ui(self):
        self.resize(760, 540)
        self.setWindowTitle("MoodPet")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow)
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowOpacity(1)

        self.status_label = QLabel("", self)
        self.status_label.setGeometry(28, 18, 310, 42)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet(
            "QLabel {"
            "font: 11pt 'Microsoft YaHei';"
            "font-weight: 700;"
            "color: #65ffd8;"
            "background-color: #102943;"
            "border: 3px solid #071927;"
            "border-radius: 10px;"
            "padding: 6px 14px;"
            "}"
        )

        self.bubble = QLabel("", self)
        self.bubble.setGeometry(26, 76, 344, 82)
        self.bubble.setWordWrap(True)
        self.bubble.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.bubble.setStyleSheet(
            "QLabel {"
            "font: 12pt 'Microsoft YaHei';"
            "font-weight: 700;"
            "color: #111318;"
            "background-color: rgba(255, 250, 244, 235);"
            "border: 3px solid #d45b5b;"
            "border-radius: 8px;"
            "padding: 10px 14px;"
            "}"
        )
        self.bubble.mousePressEvent = self._bubble_clicked

        self.label = QLabel("", self)
        self.label.setGeometry(82, 234, 200, 200)
        self.Action(str(BASE_DIR / "pet" / "init" / "start.gif"))

        self.tip_label = QLabel("拖拽只改变位置\n双击打开功能导航", self)
        self.tip_label.setGeometry(24, 164, 258, 58)
        self.tip_label.setAlignment(Qt.AlignCenter)
        self.tip_label.setStyleSheet(
            "QLabel {"
            "font: 9pt 'Microsoft YaHei';"
            "font-weight: 700;"
            "color: #65ffd8;"
            "background-color: rgba(16, 41, 67, 235);"
            "border: 2px dashed #65ffd8;"
            "border-radius: 8px;"
            "padding: 6px;"
            "}"
        )

        self.navigation_panel = QFrame(self)
        self.navigation_panel.setGeometry(346, 26, 388, 480)
        self.navigation_panel.setVisible(False)
        self.navigation_panel.setStyleSheet(
            "QFrame {"
            "background-color: #fff1da;"
            "border: 4px solid #071927;"
            "border-radius: 12px;"
            "}"
            "QLabel {"
            "border: none;"
            "color: #111318;"
            "font: 11pt 'Microsoft YaHei';"
            "font-weight: 700;"
            "}"
            "QPushButton {"
            "background-color: #b9ed9e;"
            "color: #071927;"
            "border: 3px solid #071927;"
            "border-radius: 10px;"
            "font: 14pt 'Microsoft YaHei';"
            "font-weight: 700;"
            "padding: 8px 10px;"
            "text-align: left;"
            "}"
            "QPushButton:hover {"
            "background-color: #d8ffd1;"
            "}"
            "QPushButton:pressed {"
            "padding-left: 12px;"
            "padding-top: 10px;"
            "}"
        )
        self.refresh_navigation_panel()

    def _init_tray(self):
        iconpath = str(BASE_DIR / "mypetico.ico")
        quit_action = QAction("退出", self, triggered=self.quit)
        quit_action.setIcon(QIcon(iconpath))

        self.tray_icon_menu = QMenu(self)
        self.tray_icon_menu.addAction(quit_action)
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(iconpath))
        self.tray_icon.setContextMenu(self.tray_icon_menu)
        self.tray_icon.show()

    def _init_pet_actions(self):
        pet_dir = BASE_DIR / "pet"
        self.pet1 = []
        for item in os.listdir(pet_dir):
            path = pet_dir / item
            if path.is_file() and path.suffix.lower() == ".gif":
                self.pet1.append(str(path))

    def _init_timers(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.randomAct)
        self.timer.start(5000)

        self.emotion_timer = QTimer(self)
        self.emotion_timer.timeout.connect(self.poll_emotion_result)
        self.emotion_timer.start(500)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_follow_mouse = True
            self.drag_started = False
            self.mouse_drag_pos = event.globalPos() - self.pos()
            self.mouse_press_global_pos = event.globalPos()
            event.accept()
            self.setCursor(QCursor(Qt.ClosedHandCursor))
            self.Action(str(BASE_DIR / "pet" / "init" / "move.gif"))

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and self.is_follow_mouse:
            if (event.globalPos() - self.mouse_press_global_pos).manhattanLength() > 6:
                self.drag_started = True
            self.move(event.globalPos() - self.mouse_drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.RightButton:
            return
        self.Action(str(BASE_DIR / "pet" / "init" / "stay.gif"))
        self.is_follow_mouse = False
        self.setCursor(Qt.OpenHandCursor)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton and should_open_navigation(2, self.drag_started):
            self.toggle_navigation_panel()
            event.accept()

    def enterEvent(self, event):
        self.setCursor(Qt.OpenHandCursor)

    def execute_action(self, action_config):
        if action_config["type"] == "subprocess.run":
            subprocess.run(action_config["params"], shell=True)
        elif action_config["type"] == "webbrowser":
            webbrowser.open(action_config["params"])
        elif action_config["type"] == "subprocess.Popen":
            subprocess.Popen(action_config["params"], creationflags=subprocess.CREATE_NEW_CONSOLE)

    def load_menu_config(self):
        config_path = BASE_DIR / "config" / "menu_config.json"
        try:
            with open(config_path, "r", encoding="utf-8") as config:
                return json.load(config)
        except Exception as exc:
            self.log.warning("Failed to load menu config: %s", exc)
            return {}

    def refresh_navigation_panel(self):
        for child in self.navigation_panel.findChildren((QLabel, QPushButton)):
            child.setParent(None)
            child.deleteLater()

        for child in self.navigation_panel.findChildren(QFrame):
            child.setParent(None)
            child.deleteLater()

        header = QFrame(self.navigation_panel)
        header.setGeometry(0, 0, 388, 58)
        header.setStyleSheet(
            "QFrame {"
            "background-color: #58d2bd;"
            "border: none;"
            "border-bottom: 4px solid #071927;"
            "border-top-left-radius: 8px;"
            "border-top-right-radius: 8px;"
            "}"
        )

        title = QLabel("✿ 功能导航", header)
        title.setGeometry(18, 10, 210, 34)
        title.setStyleSheet("font: 17pt 'Microsoft YaHei'; font-weight: 900; color: #071927;")

        close_button = QPushButton("", header)
        close_button.setGeometry(336, 10, 34, 34)
        apply_button_icon(close_button, "close", 24)
        close_button.setStyleSheet(
            "QPushButton {"
            "background-color: #ff4545;"
            "color: white;"
            "border: 3px solid #071927;"
            "border-radius: 6px;"
            "font: 20pt 'Microsoft YaHei';"
            "font-weight: 900;"
            "padding: 0;"
            "text-align: center;"
            "}"
            "QPushButton:hover { background-color: #ff6868; }"
        )
        close_button.clicked.connect(self.navigation_panel.hide)

        hero = QLabel(self.navigation_panel)
        hero.setGeometry(126, 72, 136, 116)
        hero_movie = QMovie(str(BASE_DIR / "pet" / "init" / "stay.gif"))
        hero_movie.setScaledSize(QSize(124, 124))
        hero.setMovie(hero_movie)
        hero_movie.start()
        self.navigation_hero_movie = hero_movie

        prompt = QLabel("选择你想使用的功能", self.navigation_panel)
        prompt.setGeometry(88, 188, 220, 30)
        prompt.setAlignment(Qt.AlignCenter)
        prompt.setStyleSheet("font: 15pt 'Microsoft YaHei'; font-weight: 900; color: #111318;")

        modules = build_feature_modules(self.load_menu_config(), self.emotion_enabled)
        positions = [(28, 226), (204, 226), (28, 334), (204, 334)]
        for module, (x, y) in zip(modules, positions):
            button = self._create_module_button(module, x, y)
            button.clicked.connect(lambda checked=False, module_id=module["id"]: self.open_feature_module(module_id))

        footer = QFrame(self.navigation_panel)
        footer.setGeometry(0, 438, 388, 42)
        footer.setStyleSheet(
            "QFrame {"
            "background-color: #102943;"
            "border: none;"
            "border-top: 4px solid #071927;"
            "border-bottom-left-radius: 8px;"
            "border-bottom-right-radius: 8px;"
            "}"
        )
        status = QLabel("♥ MoodPet 陪伴中", footer)
        status.setGeometry(18, 7, 230, 28)
        status.setStyleSheet("font: 12pt 'Microsoft YaHei'; font-weight: 900; color: #ffd77d;")

        signal = QLabel("▂▄▆█", footer)
        signal.setGeometry(310, 7, 58, 28)
        signal.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        signal.setStyleSheet("font: 15pt 'Microsoft YaHei'; font-weight: 900; color: #91f18b;")

    def _create_module_button(self, module, x, y):
        colors = {
            "mint": ("#dbffd0", "#a9e996"),
            "pink": ("#ffc9d4", "#f58ca2"),
            "lilac": ("#ead7ff", "#b99cf4"),
            "sky": ("#d9f0ff", "#92d0f2"),
        }
        icon_colors = {
            "mint": "#0b9f8f",
            "pink": "#263a54",
            "lilac": "#293266",
            "sky": "#30415c",
        }
        start_color, end_color = colors.get(module["accent"], colors["mint"])
        icon_color = icon_colors.get(module["accent"], "#071927")

        shadow = QFrame(self.navigation_panel)
        shadow.setGeometry(x + 4, y + 6, 156, 94)
        shadow.setStyleSheet(
            "QFrame {"
            "background-color: #273047;"
            "border: 3px solid #071927;"
            "border-radius: 10px;"
            "}"
        )
        self._bind_module_click(shadow, module["id"])

        card = QFrame(self.navigation_panel)
        card.setGeometry(x, y, 156, 94)
        card.setStyleSheet(
            "QFrame {"
            f"background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {start_color}, stop:1 {end_color});"
            "border: 3px solid #071927;"
            "border-radius: 10px;"
            "}"
        )
        self._bind_module_click(card, module["id"])

        icon = QLabel(card)
        icon.setGeometry(0, 10, 156, 38)
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet("QLabel { border: none; background: transparent; }")
        apply_label_icon(icon, module.get("icon_feature", "navigation"), 40, icon_color)
        self._bind_module_click(icon, module["id"])

        title = QLabel(module["title"], card)
        title.setGeometry(0, 54, 128, 32)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            "QLabel {"
            "border: none;"
            "background: transparent;"
            "color: #071927;"
            "font: 16pt 'Microsoft YaHei';"
            "font-weight: 900;"
            "}"
        )
        self._bind_module_click(title, module["id"])

        arrow = QLabel("›", card)
        arrow.setGeometry(124, 54, 20, 32)
        arrow.setAlignment(Qt.AlignCenter)
        arrow.setStyleSheet(
            "QLabel {"
            "border: none;"
            "background: transparent;"
            "color: #071927;"
            "font: 19pt 'Microsoft YaHei';"
            "font-weight: 900;"
            "}"
        )
        self._bind_module_click(arrow, module["id"])

        button = QPushButton("", card)
        button.setGeometry(0, 0, 156, 94)
        button.setToolTip(f"{module['description']}，{module['cta']}")
        button.setStyleSheet(
            "QPushButton {"
            "background-color: rgba(255, 255, 255, 0);"
            "border: none;"
            "}"
            "QPushButton:hover { background-color: rgba(255, 255, 255, 36); }"
            "QPushButton:pressed { background-color: rgba(7, 25, 39, 18); }"
        )
        return button

    def _bind_module_click(self, widget, module_id):
        widget.setCursor(Qt.PointingHandCursor)

        def open_module(event, selected_module_id=module_id):
            if event.button() == Qt.LeftButton:
                self.open_feature_module(selected_module_id)
                event.accept()

        widget.mousePressEvent = open_module

    def open_feature_module(self, module_id):
        if module_id == "realtime":
            self.open_realtime_monitor()
        elif module_id == "todo":
            self.open_todo_panel()
        elif module_id == "games":
            self.open_game_entry()
        elif module_id == "settings":
            self.open_settings_panel()

    def open_actions_menu(self):
        menu = QMenu("待办", self)
        for group in build_navigation_groups(self.load_menu_config()):
            submenu = menu.addMenu(group["title"])
            for action_config in group["items"]:
                action = submenu.addAction(action_config["name"])
                action.triggered.connect(lambda checked=False, config=action_config: self.execute_action(config))
        menu.exec_(self.mapToGlobal(self.navigation_panel.pos()) + self.navigation_panel.rect().center())

    def open_todo_panel(self):
        if self.todo_panel is None:
            self.todo_panel = TodoPanelWindow(BASE_DIR, parent=None)
        self.todo_panel.refresh()
        self.todo_panel.show()
        self.todo_panel.raise_()
        self.todo_panel.activateWindow()

    def open_game_entry(self):
        if self.mini_game_panel is None:
            self.mini_game_panel = MiniGamePanelWindow(BASE_DIR, parent=None)
        self.mini_game_panel.refresh()
        self.mini_game_panel.show()
        self.mini_game_panel.raise_()
        self.mini_game_panel.activateWindow()

    def open_settings_folder(self):
        config_dir = BASE_DIR / "config"
        if hasattr(os, "startfile"):
            os.startfile(str(config_dir))
        else:
            subprocess.Popen(["explorer", str(config_dir)])

    def open_settings_panel(self):
        if self.settings_panel is None:
            self.settings_panel = SettingsPanelWindow(
                BASE_DIR,
                get_camera_enabled=lambda: self.emotion_enabled,
                toggle_recognition=self.toggle_emotion_recognition,
                parent=None,
                on_settings_change=self.apply_panel_settings,
                open_target=self.open_feature_module,
            )
        self.settings_panel.refresh()
        self.settings_panel.show()
        self.settings_panel.raise_()
        self.settings_panel.activateWindow()

    def open_realtime_monitor(self):
        if self.realtime_monitor is None:
            self.realtime_monitor = RealtimeMonitorWindow(
                BASE_DIR,
                get_state=lambda: self.current_emotion_state,
                is_enabled=lambda: self.emotion_enabled,
                toggle_recognition=self.toggle_emotion_recognition,
                parent=None,
            )
        self.realtime_monitor.refresh()
        self.realtime_monitor.show()
        self.realtime_monitor.raise_()
        self.realtime_monitor.activateWindow()

    def toggle_navigation_panel(self):
        self.refresh_navigation_panel()
        self.navigation_panel.setVisible(self.navigation_panel.isHidden())
        if not self.navigation_panel.isHidden():
            self.navigation_panel.raise_()

    def contextMenuEvent(self, event):
        root_menu = QMenu("MoodPet", self)

        emotion_action = root_menu.addAction("关闭情绪识别" if self.emotion_enabled else "开启情绪识别")
        root_menu.addSeparator()

        actions = []
        action_configs = []
        self._append_config_menus(root_menu, actions, action_configs)

        root_menu.addSeparator()
        quit_action = root_menu.addAction("退出")
        selected_action = root_menu.exec_(self.mapToGlobal(event.pos()))

        if selected_action == emotion_action:
            self.toggle_emotion_recognition()
        elif selected_action in actions:
            self.execute_action(action_configs[actions.index(selected_action)])
        elif selected_action == quit_action:
            self.quit()

    def _append_config_menus(self, root_menu, actions, action_configs):
        for menu_name, items in self.load_menu_config().items():
            submenu = root_menu.addMenu(str(menu_name))
            for action_config in items:
                action_configs.append(action_config)
                actions.append(submenu.addAction(action_config["name"]))

    def toggle_emotion_recognition(self):
        if self.emotion_enabled:
            self.emotion_worker.stop()
            self.emotion_enabled = False
            self.show_emotion_state(build_emotion_state("disabled", message="情绪识别已关闭。"))
            self.refresh_navigation_panel()
            if self.realtime_monitor is not None:
                self.realtime_monitor.refresh()
            if self.settings_panel is not None:
                self.settings_panel.refresh()
            return

        self.emotion_enabled = True
        self.show_emotion_state(build_emotion_state("unknown", message="正在启动摄像头情绪识别..."))
        self.refresh_navigation_panel()
        if self.realtime_monitor is not None:
            self.realtime_monitor.refresh()
        if self.settings_panel is not None:
            self.settings_panel.refresh()
        self.emotion_worker.start()

    def poll_emotion_result(self):
        try:
            while True:
                state = self.emotion_queue.get_nowait()
                self.show_emotion_state(state)
        except queue.Empty:
            pass

    def show_emotion_state(self, state):
        self.current_emotion_state = state
        self.status_label.setText("● " + camera_status_text(self.emotion_enabled, state.emotion))
        if state.emotion in {"disabled", "error"}:
            self.bubble.setText(pet_bubble_text(state))
            self.last_bubble_emit_seconds = None
        else:
            now_seconds = time.time()
            if can_emit_bubble(self.bubble_settings, now_seconds, self.last_bubble_emit_seconds):
                context = BubbleContext(emotion_state=state, settings=self.bubble_settings)
                reply = build_bubble_reply(context)
                self.bubble.setText(reply.text)
                self.active_bubble_target_id = reply.target_id
                self.last_bubble_emit_seconds = now_seconds
        if self.realtime_monitor is not None:
            self.realtime_monitor.refresh()

    def apply_panel_settings(self, state):
        self.bubble_settings = BubbleSettings(
            frequency=state.bubble_frequency,
            do_not_disturb=state.bubble_do_not_disturb,
            jump_target=state.jump_target,
        )
        self.active_bubble_target_id = state.jump_target

    def _bubble_clicked(self, event):
        if event.button() == Qt.LeftButton:
            self.open_feature_module(self.active_bubble_target_id)
            event.accept()

    def quit(self):
        self.emotion_worker.stop()
        app = QApplication.instance()
        if app is not None:
            app.quit()
        self.close()

    def Action(self, action):
        self.movie = QMovie(action)
        self.movie.setScaledSize(QSize(200, 200))
        self.label.setMovie(self.movie)
        self.movie.start()

    def randomAct(self):
        if self.pet1 and not self.condition:
            self.Action(random.choice(self.pet1))
            self.condition = 1
        else:
            self.Action(str(BASE_DIR / "pet" / "init" / "stay.gif"))
            self.condition = 0
        self.timer.start(random.randint(10, 30) * 1000)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(str(BASE_DIR / "mypetico.ico")))
    mainWin = DemoWin()
    mainWin.show()
    sys.exit(app.exec_())
