import unittest

from moodpet.emotion import best_emotion, best_openvino_emotion, build_emotion_state, emotion_to_zh


class EmotionMappingTest(unittest.TestCase):
    def test_translates_supported_emotions_to_chinese(self):
        self.assertEqual(emotion_to_zh("happy"), "开心")
        self.assertEqual(emotion_to_zh("neutral"), "平静")
        self.assertEqual(emotion_to_zh("sad"), "低落")
        self.assertEqual(emotion_to_zh("fear"), "紧张")

    def test_unknown_emotion_uses_unknown_label(self):
        self.assertEqual(emotion_to_zh("confused"), "未知")

    def test_builds_display_text_with_chinese_label_and_confidence(self):
        state = build_emotion_state("happy", 0.823)

        self.assertEqual(state.label_zh, "开心")
        self.assertIn("情绪：开心（82%）", state.display_text())

    def test_marks_missing_face_as_away(self):
        state = build_emotion_state("happy", 0.9, face_detected=False)

        self.assertEqual(state.emotion, "away")
        self.assertEqual(state.label_zh, "离开")
        self.assertIn("状态：离开", state.display_text())

    def test_selects_highest_scored_emotion(self):
        state = best_emotion({"happy": 12.0, "neutral": 65.0, "sad": 23.0})

        self.assertEqual(state.emotion, "neutral")
        self.assertEqual(state.label_zh, "平静")
        self.assertEqual(state.confidence, 0.65)

    def test_openvino_keeps_clear_happy_expression(self):
        state = best_openvino_emotion({"happy": 0.65, "sad": 0.14, "neutral": 0.12})

        self.assertEqual(state.emotion, "happy")

    def test_openvino_keeps_surprise_expression(self):
        state = best_openvino_emotion({"surprise": 0.7, "neutral": 0.2})

        self.assertEqual(state.emotion, "surprise")

    def test_openvino_maps_anger_to_angry_state(self):
        state = best_openvino_emotion({"anger": 0.5, "neutral": 0.3})

        self.assertEqual(state.emotion, "angry")

    def test_openvino_keeps_neutral_when_neutral_leads(self):
        state = best_openvino_emotion({"neutral": 0.74, "sad": 0.21, "happy": 0.02})

        self.assertEqual(state.emotion, "neutral")


if __name__ == "__main__":
    unittest.main()
