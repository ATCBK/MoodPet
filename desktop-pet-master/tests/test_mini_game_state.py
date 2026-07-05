import unittest

from moodpet.mini_game_state import (
    MiniGameState,
    available_choices,
    build_default_game,
    choose_event,
    collected_count_text,
    continue_story,
    current_node,
    progress_text,
    restart_game,
)


class MiniGameStateTest(unittest.TestCase):
    def test_default_story_starts_at_event_step_with_initial_clues(self):
        state = build_default_game()

        self.assertEqual(state.story_title, "雾中的小邮局")
        self.assertEqual(progress_text(state), "流程 2/6")
        self.assertEqual(collected_count_text(state), "3 / 6")
        self.assertEqual(
            [clue.title for clue in state.clues if clue.collected],
            ["蓝色邮票", "慢半拍的钟声", "未写完的地址"],
        )

    def test_choice_starts_a_six_step_route_without_skipping(self):
        state = choose_event(build_default_game(), "clock")

        seen = [(progress_text(state), current_node(state).title)]
        while state.node_index < len(state.nodes) - 1:
            state = continue_story(state)
            seen.append((progress_text(state), current_node(state).title))

        self.assertEqual(
            seen,
            [
                ("流程 3/6", "钟声里的暗号"),
                ("流程 4/6", "亮起的信箱格"),
                ("流程 5/6", "确认投递方向"),
                ("流程 6/6", "雾散后的投递"),
            ],
        )

    def test_each_choice_keeps_its_own_content_through_the_route(self):
        expected_routes = {
            "pick_letter": ["回信背面的日期", "旧蜡封的保存痕迹", "补全回信地址", "雾散后的投递"],
            "clock": ["钟声里的暗号", "亮起的信箱格", "确认投递方向", "雾散后的投递"],
            "ask_pet": ["薄荷香的方向", "旧书架旁的通讯录", "确认投递方向", "雾散后的投递"],
        }

        for choice_id, expected_titles in expected_routes.items():
            state = choose_event(build_default_game(), choice_id)
            titles = [current_node(state).title]
            while state.node_index < len(state.nodes) - 1:
                state = continue_story(state)
                titles.append(current_node(state).title)
            self.assertEqual(titles, expected_titles)

    def test_choose_event_collects_branch_clue_and_records_choice(self):
        state = build_default_game()

        next_state = choose_event(state, "ask_pet")

        self.assertIsNot(state, next_state)
        self.assertEqual(next_state.node_index, 2)
        self.assertEqual(next_state.selected_choice_id, "ask_pet")
        self.assertEqual(current_node(next_state).title, "薄荷香的方向")
        self.assertIn("信封边缘的薄荷香", [clue.title for clue in next_state.clues if clue.collected])
        self.assertEqual(progress_text(next_state), "流程 3/6")

    def test_unknown_choice_keeps_state_unchanged(self):
        state = build_default_game()

        self.assertEqual(choose_event(state, "missing-choice"), state)

    def test_available_choices_are_empty_after_route_starts(self):
        state = choose_event(build_default_game(), "pick_letter")

        self.assertTrue(state.interaction_done)
        self.assertEqual(available_choices(state), [])

    def test_restart_restores_initial_story_state(self):
        state = continue_story(choose_event(build_default_game(), "clock"))

        restarted = restart_game(state)

        self.assertIsInstance(restarted, MiniGameState)
        self.assertEqual(restarted.node_index, 1)
        self.assertFalse(restarted.interaction_done)
        self.assertEqual(restarted.selected_choice_id, "")
        self.assertEqual(collected_count_text(restarted), "3 / 6")


if __name__ == "__main__":
    unittest.main()
