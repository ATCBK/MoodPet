import queue
import time
import unittest

from moodpet.bubble_async import AsyncBubbleReplyRunner
from moodpet.bubble_policy import BubbleContext, BubbleReply, BubbleSettings
from moodpet.emotion import build_emotion_state


class SlowProvider:
    def generate(self, context):
        time.sleep(0.2)
        return BubbleReply("后台生成好了", "todo", "model")


class BrokenProvider:
    def generate(self, context):
        raise RuntimeError("network down")


class BubbleAsyncTest(unittest.TestCase):
    def test_request_returns_immediately_and_publishes_reply_later(self):
        result_queue = queue.Queue()
        runner = AsyncBubbleReplyRunner(result_queue)
        context = BubbleContext(build_emotion_state("sad", 0.7), BubbleSettings())

        started = time.perf_counter()
        runner.request(7, context, SlowProvider())
        elapsed = time.perf_counter() - started

        self.assertLess(elapsed, 0.05)
        request_id, reply = result_queue.get(timeout=1)
        self.assertEqual(request_id, 7)
        self.assertEqual(reply.text, "后台生成好了")
        self.assertEqual(reply.target_id, "todo")

    def test_worker_publishes_local_fallback_when_provider_crashes(self):
        result_queue = queue.Queue()
        runner = AsyncBubbleReplyRunner(result_queue)
        context = BubbleContext(build_emotion_state("sad", 0.7), BubbleSettings())

        runner.request(8, context, BrokenProvider())

        request_id, reply = result_queue.get(timeout=1)
        self.assertEqual(request_id, 8)
        self.assertEqual(reply.source, "local")
        self.assertTrue(reply.text)


if __name__ == "__main__":
    unittest.main()
