import os
import sys
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPixmap
from PyQt5.QtWidgets import QApplication

from moodpet.mini_game_panel import MiniGamePanelWindow, PostalScene


class MiniGamePanelTest(unittest.TestCase):
    def test_postal_scene_accepts_generated_image_path_for_main_render(self):
        app = QApplication.instance() or QApplication(sys.argv)
        scene = PostalScene(None)
        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "choice.png"
            pixmap = QPixmap(32, 32)
            pixmap.fill(QColor("#ff6374"))
            self.assertTrue(pixmap.save(str(image_path)))

            scene.set_image_path(image_path)

            self.assertEqual(scene.image_path, image_path)
            self.assertFalse(scene.scene_pixmap.isNull())
        app.processEvents()

    def test_minigame_layout_keeps_only_story_image_and_choices(self):
        app = QApplication.instance() or QApplication(sys.argv)
        window = MiniGamePanelWindow(Path(__file__).resolve().parents[1])
        window.show()
        app.processEvents()

        self.assertGreaterEqual(window.scene.width(), 620)
        self.assertGreaterEqual(window.scene.height(), 360)
        self.assertGreaterEqual(window.event_panel.height(), 360)
        self.assertFalse(hasattr(window, "clue_panel"))
        self.assertFalse(hasattr(window, "interaction_panel"))
        self.assertFalse(hasattr(window, "pet_note"))
        self.assertTrue(hasattr(window, "task_panel"))
        self.assertIs(window.task_panel.parent(), window.event_panel)
        self.assertGreater(window.task_panel.y(), 300)
        self.assertTrue(window.restart_button.isVisible())
        self.assertTrue(window.back_button.isVisible())

        window.close()
        app.processEvents()


if __name__ == "__main__":
    unittest.main()
