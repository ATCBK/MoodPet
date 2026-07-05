import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtWidgets import QApplication, QLabel


def test_focus_button_starts_timer_without_adding_todo():
    from moodpet.todo_panel import TodoPanelWindow

    app = QApplication.instance() or QApplication(sys.argv)
    window = TodoPanelWindow(Path(__file__).resolve().parents[1])
    original_count = len(window.todos)

    window._focus_done()
    app.processEvents()

    assert len(window.todos) == original_count
    assert window.focus_remaining_seconds == 25 * 60
    assert window.focus_timer.isActive()
    assert window.focus_button.text() == "专注中"
    assert window.focus_time_label.text() == "25:00"

    window.focus_timer.stop()
    window.close()


def test_todo_panel_visible_labels_are_real_chinese():
    from moodpet.todo_panel import TodoPanelWindow

    app = QApplication.instance() or QApplication(sys.argv)
    window = TodoPanelWindow(Path(__file__).resolve().parents[1])

    texts = {label.text() for label in window.findChildren(QLabel)}

    assert "待办" in texts
    assert "为你推荐" in texts
    assert "番茄钟专注 25 分钟" in texts

    window.close()
