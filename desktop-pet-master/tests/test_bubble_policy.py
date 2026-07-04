import unittest

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
from moodpet.emotion import build_emotion_state


class FakeModelProvider(BubbleReplyProvider):
    def generate(self, context: BubbleContext) -> BubbleReply:
        return BubbleReply(text="  先去待办页完成一个小任务，然后回来休息。  ", target_id="todo")


class BubblePolicyTest(unittest.TestCase):
    def test_frequency_cooldown_uses_configured_minutes(self):
        settings = BubbleSettings(frequency="medium")

        self.assertTrue(can_emit_bubble(settings, now_seconds=300, last_emit_seconds=0))
        self.assertFalse(can_emit_bubble(settings, now_seconds=120, last_emit_seconds=0))

    def test_do_not_disturb_blocks_short_repeated_emotion_bubbles(self):
        settings = BubbleSettings(frequency="high", do_not_disturb=True)

        self.assertFalse(can_emit_bubble(settings, now_seconds=50, last_emit_seconds=10))
        self.assertTrue(can_emit_bubble(settings, now_seconds=400, last_emit_seconds=10))

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


if __name__ == "__main__":
    unittest.main()
