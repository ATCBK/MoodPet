import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QLabel

from main import DemoWin


def test_visible_navigation_card_text_triggers_module_open():
    app = QApplication.instance() or QApplication([])
    win = DemoWin()
    opened = []
    win.open_feature_module = lambda module_id: opened.append(module_id)

    win.toggle_navigation_panel()
    title_label = next(label for label in win.navigation_panel.findChildren(QLabel) if label.text() == "实时检测")

    QTest.mouseClick(title_label, Qt.LeftButton, pos=title_label.rect().center())

    assert opened == ["realtime"]
    win.quit()


def test_navigation_panel_hides_after_module_is_selected():
    app = QApplication.instance() or QApplication([])
    win = DemoWin()
    opened = []
    win.open_realtime_monitor = lambda: opened.append("realtime")

    win.toggle_navigation_panel()
    assert not win.navigation_panel.isHidden()

    title_label = next(label for label in win.navigation_panel.findChildren(QLabel) if label.text() == "实时检测")
    QTest.mouseClick(title_label, Qt.LeftButton, pos=title_label.rect().center())

    assert opened == ["realtime"]
    assert win.navigation_panel.isHidden()
    win.quit()


def test_default_page_does_not_show_drag_instruction_label():
    app = QApplication.instance() or QApplication([])
    win = DemoWin()

    visible_texts = [label.text() for label in win.findChildren(QLabel) if label.isVisible()]

    assert "拖拽只改变位置\n双击打开功能导航" not in visible_texts
    win.quit()
