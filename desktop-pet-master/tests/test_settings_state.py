import unittest

from moodpet.settings_state import (
    SettingsState,
    apply_camera_selection,
    apply_frequency,
    apply_jump_target,
    autostart_status_text,
    available_cameras,
    camera_status_text,
    frequency_description,
    frequency_label,
    jump_target_label,
    privacy_status_text,
    voice_status_text,
)


class SettingsStateTest(unittest.TestCase):
    def test_available_cameras_uses_default_when_input_is_empty(self):
        self.assertEqual(available_cameras(["", "  "]), ["Integrated Camera", "Mock Camera"])

    def test_camera_selection_keeps_known_camera_and_falls_back_unknown_camera(self):
        state = SettingsState(camera_name="Integrated Camera")

        selected = apply_camera_selection(state, "USB Camera", ["Integrated Camera", "USB Camera"])
        fallback = apply_camera_selection(state, "Missing", ["Integrated Camera", "USB Camera"])

        self.assertEqual(selected.camera_name, "USB Camera")
        self.assertEqual(fallback.camera_name, "Integrated Camera")

    def test_frequency_label_and_description_default_to_recommended_mode(self):
        self.assertEqual(frequency_label("medium"), "适中（推荐）")
        self.assertEqual(frequency_description("medium"), "每隔 2~5 分钟")
        self.assertEqual(frequency_label("unknown"), "适中（推荐）")

    def test_apply_frequency_rejects_unknown_values(self):
        state = SettingsState(bubble_frequency="low")

        self.assertEqual(apply_frequency(state, "high").bubble_frequency, "high")
        self.assertEqual(apply_frequency(state, "fastest").bubble_frequency, "medium")

    def test_jump_target_defaults_and_rejects_unknown_values(self):
        state = SettingsState(jump_target="todo")

        self.assertEqual(jump_target_label("games"), "去小游戏")
        self.assertEqual(jump_target_label("unknown"), "去待办")
        self.assertEqual(apply_jump_target(state, "games").jump_target, "games")
        self.assertEqual(apply_jump_target(state, "missing").jump_target, "todo")

    def test_status_text_reflects_all_switches(self):
        state = SettingsState(
            camera_enabled=True,
            voice_enabled=False,
            privacy_enabled=True,
            autostart_enabled=True,
        )

        self.assertEqual(camera_status_text(state), "摄像头已开启")
        self.assertEqual(voice_status_text(state), "语音功能已关闭")
        self.assertEqual(privacy_status_text(state), "隐私模式已开启")
        self.assertEqual(autostart_status_text(state), "开机自启动已开启")


if __name__ == "__main__":
    unittest.main()
