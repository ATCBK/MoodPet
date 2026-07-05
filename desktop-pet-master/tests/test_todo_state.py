import unittest
from datetime import date

from moodpet.todo_state import (
    DEFAULT_TODOS,
    TodoItem,
    add_todo,
    assistant_message,
    completion_ratio,
    completion_text,
    fatigue_level,
    today_label,
    toggle_completed,
    toggle_starred,
    visible_todos,
)


class TodoStateTest(unittest.TestCase):
    def test_default_progress_matches_reference_screen(self):
        self.assertEqual(completion_text(DEFAULT_TODOS), "已完成 1/4")
        self.assertEqual(completion_ratio(DEFAULT_TODOS), 0.25)

    def test_today_label_uses_chinese_weekday(self):
        self.assertEqual(today_label(date(2024, 5, 20)), "今天是 2024/05/20 星期一")

    def test_completed_tab_only_returns_done_items(self):
        rows = visible_todos(DEFAULT_TODOS, tab="completed")

        self.assertEqual([item.title for item in rows], ["喝一杯水"])

    def test_sorting_can_prioritize_starred_tasks(self):
        rows = visible_todos(DEFAULT_TODOS, sort_mode="starred")

        self.assertEqual(rows[0].title, "喝一杯水")

    def test_add_todo_ignores_blank_titles_and_appends_clean_task(self):
        self.assertEqual(add_todo(DEFAULT_TODOS, "   "), list(DEFAULT_TODOS))

        rows = add_todo(DEFAULT_TODOS, "  写周报  ", "工作", "17:00")

        self.assertEqual(rows[-1], TodoItem(5, "写周报", "工作", "17:00"))

    def test_toggle_completed_sets_completion_time_and_can_reopen(self):
        rows = toggle_completed(DEFAULT_TODOS, 1, "10:05")

        self.assertTrue(rows[0].completed)
        self.assertEqual(rows[0].completed_at, "10:05")

        reopened = toggle_completed(rows, 1, "10:06")

        self.assertFalse(reopened[0].completed)
        self.assertEqual(reopened[0].completed_at, "")

    def test_toggle_starred_flips_star_state(self):
        rows = toggle_starred(DEFAULT_TODOS, 1)

        self.assertTrue(rows[0].starred)

    def test_assistant_message_and_fatigue_level_reflect_remaining_work(self):
        self.assertIn("小任务", assistant_message(DEFAULT_TODOS))
        self.assertEqual(fatigue_level(completed_count=1, total_count=4), 72)

        done = [TodoItem(1, "休息", "生活", "今天", completed=True)]

        self.assertIn("奖励", assistant_message(done))


if __name__ == "__main__":
    unittest.main()
