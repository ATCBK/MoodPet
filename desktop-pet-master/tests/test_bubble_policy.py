import unittest
from unittest.mock import patch

from moodpet.bubble_policy import (
    BubbleContext,
    BubbleReply,
    BubbleReplyProvider,
    BubbleSettings,
    CallableModelClient,
    ColdStartBubbleProvider,
    LocalRuleBubbleProvider,
    ModelBubbleProvider,
    build_model_prompt,
    build_bubble_reply,
    can_emit_bubble,
    sanitize_user_bubble_reply,
    target_for_emotion,
)
from moodpet.deepseek_bubble import DeepSeekBubbleClient, build_default_bubble_provider, load_env_file
from moodpet.emotion import build_emotion_state


class FakeModelProvider(BubbleReplyProvider):
    def generate(self, context: BubbleContext) -> BubbleReply:
        return BubbleReply(text="  先去待办页完成一个小任务，然后回来休息。  ", target_id="todo")


class BubblePolicyTest(unittest.TestCase):
    def test_frequency_cooldown_uses_short_refresh_seconds(self):
        settings = BubbleSettings(frequency="medium")

        self.assertTrue(can_emit_bubble(settings, now_seconds=5, last_emit_seconds=0))
        self.assertFalse(can_emit_bubble(settings, now_seconds=4, last_emit_seconds=0))

    def test_do_not_disturb_keeps_five_second_refresh_floor(self):
        settings = BubbleSettings(frequency="high", do_not_disturb=True)

        self.assertFalse(can_emit_bubble(settings, now_seconds=14, last_emit_seconds=10))
        self.assertTrue(can_emit_bubble(settings, now_seconds=15, last_emit_seconds=10))

    def test_target_for_emotion_prefers_todo_for_tired_or_low_emotion(self):
        self.assertEqual(target_for_emotion("sad"), "todo")
        self.assertEqual(target_for_emotion("angry"), "todo")
        self.assertEqual(target_for_emotion("happy"), "games")
        self.assertEqual(target_for_emotion("neutral"), "realtime")

    def test_local_rule_provider_builds_constrained_reply(self):
        context = BubbleContext(
            emotion_state=build_emotion_state("sad", 0.72),
            settings=BubbleSettings(frequency="medium"),
        )

        reply = build_bubble_reply(context, provider=LocalRuleBubbleProvider())

        self.assertLessEqual(len(reply.text), 36)
        self.assertEqual(reply.target_id, "todo")
        self.assertIn("小任务", reply.text)

    def test_model_provider_output_is_sanitized_through_same_contract(self):
        context = BubbleContext(
            emotion_state=build_emotion_state("happy", 0.88),
            settings=BubbleSettings(frequency="high"),
        )

        reply = build_bubble_reply(context, provider=FakeModelProvider())

        self.assertEqual(reply.text, "先去待办页完成一个小任务，然后回来休息。")
        self.assertEqual(reply.target_id, "todo")
        self.assertEqual(reply.source, "local")

    def test_user_selected_jump_target_overrides_emotion_default(self):
        context = BubbleContext(
            emotion_state=build_emotion_state("happy", 0.88),
            settings=BubbleSettings(frequency="medium", jump_target="todo"),
        )

        reply = build_bubble_reply(context, provider=LocalRuleBubbleProvider())

        self.assertEqual(reply.target_id, "todo")

    def test_model_prompt_exposes_future_llm_constraints(self):
        context = BubbleContext(
            emotion_state=build_emotion_state("sad", 0.72),
            settings=BubbleSettings(frequency="medium", jump_target="games"),
            recent_reply="先休息一下",
        )

        prompt = build_model_prompt(context)

        self.assertEqual(prompt.target_id, "games")
        self.assertEqual(prompt.max_length, 36)
        self.assertIn("不要输出诊断", prompt.safety_rule)
        self.assertEqual(prompt.recent_reply, "先休息一下")

    def test_model_provider_uses_client_and_falls_back_to_cold_start(self):
        context = BubbleContext(
            emotion_state=build_emotion_state("sad", 0.72),
            settings=BubbleSettings(frequency="medium"),
        )
        provider = ModelBubbleProvider(CallableModelClient(lambda prompt: "  我会陪你，先打开待办做一步。\n "))

        reply = build_bubble_reply(context, provider=provider)

        self.assertEqual(reply.text, "我会陪你，先打开待办做一步。")
        self.assertEqual(reply.source, "model")

        broken_provider = ModelBubbleProvider(CallableModelClient(lambda prompt: (_ for _ in ()).throw(RuntimeError())))
        fallback_reply = build_bubble_reply(context, provider=broken_provider)
        cold_reply = build_bubble_reply(context, provider=ColdStartBubbleProvider())

        self.assertEqual(fallback_reply, cold_reply)

    def test_sanitize_user_bubble_reply_trims_length_and_falls_back_empty_text(self):
        long_text = "今天先把最小的一步做完，然后我会继续陪你保持节奏，不需要一下子完成全部事情。"

        self.assertEqual(sanitize_user_bubble_reply("   "), "我在旁边陪你，先做一步就好。")
        self.assertLessEqual(len(sanitize_user_bubble_reply(long_text)), 36)

    def test_deepseek_client_posts_chat_completion_with_bubble_constraints(self):
        prompt = build_model_prompt(
            BubbleContext(
                emotion_state=build_emotion_state("sad", 0.72),
                settings=BubbleSettings(frequency="medium", jump_target="todo"),
                recent_reply="先做一个很小的任务。",
            )
        )
        captured = {}

        def fake_post(url, payload, headers, timeout):
            captured["url"] = url
            captured["payload"] = payload
            captured["headers"] = headers
            captured["timeout"] = timeout
            return {"choices": [{"message": {"content": "我陪你换个小步骤开始。"}}]}

        client = DeepSeekBubbleClient(api_key="secret", post_json=fake_post)

        self.assertEqual(client.complete(prompt), "我陪你换个小步骤开始。")
        self.assertEqual(captured["url"], "https://api.deepseek.com/chat/completions")
        self.assertEqual(captured["headers"]["Authorization"], "Bearer secret")
        self.assertEqual(captured["payload"]["model"], "deepseek-v4-flash")
        self.assertEqual(captured["payload"]["thinking"], {"type": "disabled"})
        self.assertEqual(captured["payload"]["max_tokens"], 48)
        self.assertGreater(captured["payload"]["temperature"], 0.7)
        self.assertIn("不要重复上一条", captured["payload"]["messages"][0]["content"])
        self.assertIn("低落", captured["payload"]["messages"][1]["content"])
        self.assertEqual(captured["timeout"], 3.0)

    def test_deepseek_client_rejects_empty_or_malformed_responses(self):
        prompt = build_model_prompt(BubbleContext(build_emotion_state("happy", 0.9), BubbleSettings()))
        client = DeepSeekBubbleClient(
            api_key="secret",
            post_json=lambda url, payload, headers, timeout: {"choices": [{"message": {"content": "   "}}]},
        )

        with self.assertRaises(RuntimeError):
            client.complete(prompt)

    def test_env_file_loader_and_default_provider_use_deepseek_when_key_exists(self):
        env_values = load_env_file("DEEPSEEK_API_KEY=abc\nDEEPSEEK_MODEL=deepseek-v4-flash\n")

        self.assertEqual(env_values["DEEPSEEK_API_KEY"], "abc")
        self.assertEqual(env_values["DEEPSEEK_MODEL"], "deepseek-v4-flash")

        with patch("moodpet.deepseek_bubble.os.environ", {}):
            provider = build_default_bubble_provider(env_values)

        self.assertIsInstance(provider, ModelBubbleProvider)

    def test_default_provider_falls_back_to_local_rules_without_key(self):
        with patch("moodpet.deepseek_bubble.os.environ", {}):
            provider = build_default_bubble_provider({})

        self.assertIsInstance(provider, LocalRuleBubbleProvider)


if __name__ == "__main__":
    unittest.main()
