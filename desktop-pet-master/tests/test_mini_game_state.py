import unittest

from moodpet.mini_game_state import (
    MiniGameState,
    available_choices,
    build_default_game,
    choose_event,
    complete_interaction,
    collected_count_text,
    current_node,
    progress_text,
    restart_game,
)


class MiniGameStateTest(unittest.TestCase):
    def test_default_story_starts_at_second_step_with_initial_clues(self):
        state = build_default_game()

        self.assertEqual(state.story_title, "雾中的小邮局")
        self.assertEqual(progress_text(state), "流程 2/5")
        self.assertEqual(collected_count_text(state), "3 / 5")
        self.assertEqual([clue.title for clue in state.clues if clue.collected], ["蓝色邮票", "慢半拍的钟声", "未写完的地址"])

    def test_choose_event_updates_node_and_collects_new_clue(self):
        state = build_default_game()

        next_state = choose_event(state, "ask_pet")

        self.assertIsNot(state, next_state)
        self.assertEqual(next_state.node_index, 2)
        self.assertEqual(current_node(next_state).title, "MoodPet 的嗅闻")
        self.assertIn("信封边缘的薄荷香", [clue.title for clue in next_state.clues if clue.collected])
        self.assertEqual(progress_text(next_state), "流程 3/5")

    def test_unknown_choice_keeps_state_unchanged(self):
        state = build_default_game()

        self.assertEqual(choose_event(state, "missing-choice"), state)

    def test_complete_interaction_adds_final_clue_and_unlocks_finish_node(self):
        state = choose_event(build_default_game(), "pick_letter")

        next_state = complete_interaction(state)

        self.assertTrue(next_state.interaction_done)
        self.assertEqual(next_state.node_index, 3)
        self.assertEqual(collected_count_text(next_state), "5 / 5")
        self.assertEqual(current_node(next_state).title, "选择后的回声")

    def test_available_choices_are_empty_after_interaction_is_done(self):
        state = complete_interaction(build_default_game())

        self.assertEqual(available_choices(state), [])

    def test_choose_event_finishes_choice_interaction_without_drag_step(self):
        state = choose_event(build_default_game(), "pick_letter")

        self.assertTrue(state.interaction_done)
        self.assertEqual(available_choices(state), [])
        self.assertEqual(current_node(state).title, "选择后的回声")

    def test_restart_restores_initial_story_state(self):
        state = complete_interaction(choose_event(build_default_game(), "clock"))

        restarted = restart_game(state)

        self.assertIsInstance(restarted, MiniGameState)
        self.assertEqual(restarted.node_index, 1)
        self.assertFalse(restarted.interaction_done)
        self.assertEqual(collected_count_text(restarted), "3 / 5")


if __name__ == "__main__":
    unittest.main()
