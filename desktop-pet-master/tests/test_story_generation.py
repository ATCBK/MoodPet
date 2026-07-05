import tempfile
import unittest
from pathlib import Path

from moodpet.emotion import build_emotion_state
from moodpet.story_generation import (
    DeepSeekStoryClient,
    StoryGenerationService,
    build_story_generation_prompt,
)


class StoryGenerationTest(unittest.TestCase):
    def test_prompt_includes_current_emotion_summary(self):
        state = build_emotion_state("sad", 0.82)
        prompt = build_story_generation_prompt(state)

        self.assertIn("sad", prompt)
        self.assertIn("低落", prompt)
        self.assertIn("当前情绪", prompt)

    def test_local_story_builder_adjusts_tone_for_low_mood(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            service = StoryGenerationService(None, Path(temp_dir))
            state = service.build_local_story(build_emotion_state("angry", 0.91))

            self.assertIn("邮局", state.story_title)
            self.assertIn("安抚", state.emotion_summary)
            self.assertEqual(len(state.nodes), 6)
            self.assertEqual(len(state.choices), 3)
            self.assertEqual(len(state.clues), 6)
            self.assertEqual(len(state.rewards), 3)

    def test_remote_story_client_posts_json_completion_request(self):
        captured = {}

        def fake_post(url, payload, headers, timeout):
            captured["url"] = url
            captured["payload"] = payload
            captured["headers"] = headers
            captured["timeout"] = timeout
            return {"choices": [{"message": {"content": '{"story_title":"测试邮局","subtitle":"先缓一缓","emotion_summary":"适合安抚","theme_subject":"一封信","theme_mood":"安静","theme_style":"治愈","nodes":[{"id":"opening","title":"开场","prompt":"p","scene_text":"s","pet_reply":"r","step_label":"开场"},{"id":"event","title":"事件","prompt":"p","scene_text":"s","pet_reply":"r","step_label":"事件"},{"id":"choice_result","title":"选择","prompt":"p","scene_text":"s","pet_reply":"r","step_label":"选择"},{"id":"clue_trace","title":"线索","prompt":"p","scene_text":"s","pet_reply":"r","step_label":"线索"},{"id":"action","title":"行动","prompt":"p","scene_text":"s","pet_reply":"r","step_label":"行动"},{"id":"ending","title":"结尾","prompt":"p","scene_text":"s","pet_reply":"r","step_label":"结尾"}],"choices":[{"id":"choice_1","icon":"✉","title":"先看信","next_node":2,"clue_id":"clue_1"},{"id":"choice_2","icon":"⏰","title":"听钟声","next_node":2,"clue_id":"clue_2"},{"id":"choice_3","icon":"🐾","title":"跟着走","next_node":2,"clue_id":"clue_3"}],"clues":[{"id":"clue_0","icon":"✦","title":"A","collected":true},{"id":"clue_1","icon":"✦","title":"B","collected":true},{"id":"clue_2","icon":"✦","title":"C","collected":true},{"id":"clue_3","icon":"✦","title":"D","collected":false},{"id":"clue_4","icon":"✦","title":"E","collected":false},{"id":"clue_5","icon":"✦","title":"F","collected":false}],"rewards":[{"label":"安心值","value":12,"icon":"❤"},{"label":"陪伴值","value":8,"icon":"✦"},{"label":"微光值","value":5,"icon":"◎"}]}'}}]}

        client = DeepSeekStoryClient(api_key="secret", post_json_func=fake_post)
        text = client.complete(build_story_generation_prompt(build_emotion_state("neutral", 0.6)))

        self.assertIn("测试邮局", text)
        self.assertEqual(captured["url"], "https://api.deepseek.com/chat/completions")
        self.assertEqual(captured["headers"]["Authorization"], "Bearer secret")
        self.assertIn("当前情绪", captured["payload"]["messages"][1]["content"])
        self.assertEqual(captured["timeout"], 12.0)


if __name__ == "__main__":
    unittest.main()
