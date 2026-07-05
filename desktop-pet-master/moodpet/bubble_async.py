import queue
import threading
from typing import Tuple

from moodpet.bubble_policy import BubbleContext, BubbleReply, BubbleReplyProvider, build_bubble_reply


class AsyncBubbleReplyRunner:
    def __init__(self, result_queue: "queue.Queue[Tuple[int, BubbleReply]]") -> None:
        self.result_queue = result_queue

    def request(self, request_id: int, context: BubbleContext, provider: BubbleReplyProvider) -> None:
        thread = threading.Thread(
            target=self._run,
            args=(request_id, context, provider),
            name=f"MoodPetBubbleReply-{request_id}",
            daemon=True,
        )
        thread.start()

    def _run(self, request_id: int, context: BubbleContext, provider: BubbleReplyProvider) -> None:
        try:
            reply = build_bubble_reply(context, provider=provider)
        except Exception:
            reply = build_bubble_reply(context)
        self.result_queue.put((request_id, reply))
