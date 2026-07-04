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
