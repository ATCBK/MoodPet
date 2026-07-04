import unittest
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from moodpet.emotion import build_emotion_state
from moodpet.realtime_monitor import (
    build_monitor_rows,
    build_trend_points,
    clamp_trend_values,
    confidence_percent,
    emotion_english_label,
    monitor_status_text,
    preview_badge_text,
)


class RealtimeMonitorTest(unittest.TestCase):
    def test_build_monitor_rows_matches_current_emotion_state(self):
        state = build_emotion_state("happy", 0.86)

        rows = build_monitor_rows(state, enabled=True)

        self.assertEqual([row.title for row in rows], ["当前情绪", "英文标签", "置信度", "状态"])
        self.assertEqual(rows[0].value, "开心")
        self.assertEqual(rows[1].value, "happy")
        self.assertEqual(rows[2].value, "86%")
        self.assertEqual(rows[3].value, "识别中")

    def test_confidence_uses_mock_baseline_when_state_has_no_score(self):
        state = build_emotion_state("neutral")

        self.assertEqual(confidence_percent(state), 62)

    def test_disabled_trend_still_shows_mock_curve(self):
        state = build_emotion_state("disabled")

        points = build_trend_points(state, enabled=False)

        self.assertEqual(len(points), 9)
        self.assertGreater(max(value for _, value in points), 0)
        self.assertEqual(points[0][0], "00:00")

    def test_enabled_trend_includes_current_confidence_near_end(self):
        state = build_emotion_state("sad", 0.34)

        points = build_trend_points(state, enabled=True)

        self.assertEqual(points[-2][1], 34)
        self.assertEqual(points[0][0], "00:00")
        self.assertEqual(points[-1][0], "24:00")

    def test_status_and_preview_text_cover_special_states(self):
        self.assertEqual(monitor_status_text(False, "happy"), "待开启")
        self.assertEqual(monitor_status_text(True, "away"), "未检测到人脸")
        self.assertEqual(preview_badge_text(False, build_emotion_state("disabled")), "摄像头待开启")
        self.assertEqual(preview_badge_text(True, build_emotion_state("error")), "摄像头异常")

    def test_unknown_english_label_and_clamping_are_stable(self):
        self.assertEqual(emotion_english_label("mystery"), "observing")
        self.assertEqual(clamp_trend_values([("a", -2), ("b", 101), ("c", 40)]), [("a", 0), ("b", 100), ("c", 40)])

    def test_confidence_bar_stays_inside_confidence_row(self):
        from PyQt5.QtWidgets import QApplication
        from moodpet.realtime_panel import RealtimeMonitorWindow

        app = QApplication.instance() or QApplication(sys.argv)
        state = build_emotion_state("happy", 0.86)
        window = RealtimeMonitorWindow(
            Path(__file__).resolve().parents[1],
            get_state=lambda: state,
            is_enabled=lambda: False,
            toggle_recognition=lambda: None,
        )

        confidence_row = window.row_frames[2]
        bar = window.confidence_bar
        fill = window.confidence_fill

        self.assertIs(bar.parent(), confidence_row)
        self.assertLessEqual(bar.x() + bar.width(), confidence_row.width())
        self.assertLessEqual(bar.y() + bar.height(), confidence_row.height())
        self.assertLessEqual(fill.width(), bar.width())
        app.processEvents()


if __name__ == "__main__":
    unittest.main()
