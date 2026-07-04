import unittest

from moodpet.emotion import build_emotion_state
from moodpet.ui_state import (
    build_feature_modules,
    build_navigation_groups,
    camera_status_text,
    pet_bubble_text,
    should_open_navigation,
)


class DesktopInteractionTest(unittest.TestCase):
    def test_camera_status_reflects_disabled_and_background_recognition(self):
        self.assertEqual(camera_status_text(False), "摄像头：已关闭")
        self.assertEqual(camera_status_text(True), "摄像头：后台识别中")

    def test_pet_bubble_uses_active_prompt_for_recognized_emotion(self):
        state = build_emotion_state("sad", 0.72)

        self.assertIn("你看起来有点累", pet_bubble_text(state))
        self.assertIn("小任务", pet_bubble_text(state))

    def test_pet_bubble_reports_camera_status_when_disabled(self):
        state = build_emotion_state("disabled")

        self.assertEqual(pet_bubble_text(state), "摄像头已关闭，右键可以开启后台识别。")

    def test_double_click_opens_navigation_but_drag_release_does_not(self):
        self.assertTrue(should_open_navigation(click_count=2, dragged=False))
        self.assertFalse(should_open_navigation(click_count=1, dragged=False))
        self.assertFalse(should_open_navigation(click_count=2, dragged=True))

    def test_navigation_groups_are_loaded_from_menu_config(self):
        menu_config = {
            "视频": [{"name": "我要看bilibili", "type": "webbrowser", "params": "https://www.bilibili.com/"}],
            "文件": [{"name": "代码", "type": "subprocess.run", "params": [".\\bat\\openDir.bat", "E:\\codes"]}],
        }

        groups = build_navigation_groups(menu_config)

        self.assertEqual([group["title"] for group in groups], ["视频", "文件"])
        self.assertEqual(groups[0]["items"][0]["name"], "我要看bilibili")

    def test_feature_modules_match_navigation_panel_order_and_state(self):
        menu_config = {
            "视频": [{"name": "我要看bilibili", "type": "webbrowser", "params": "https://www.bilibili.com/"}],
            "文件": [{"name": "代码", "type": "subprocess.run", "params": [".\\bat\\openDir.bat", "E:\\codes"]}],
        }

        modules = build_feature_modules(menu_config, emotion_enabled=True)

        self.assertEqual([module["title"] for module in modules], ["实时检测", "待办", "小游戏", "设置"])
        self.assertEqual(modules[0]["cta"], "关闭识别")
        self.assertEqual(modules[1]["description"], "2 个快捷功能")


if __name__ == "__main__":
    unittest.main()
