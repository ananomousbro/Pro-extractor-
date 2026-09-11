import re
import asyncio
import time
import logging
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

class TaskQueueManager:
    """
    Advanced Concurrency & Live Dynamic Queue Manager for Telegram Bots.
    - Limits max concurrent active extraction tasks (Default: 10)
    - Automatically queues subsequent users
    - Live updates waiting position in Telegram messages (#1, #2, #3...)
    - Prevents Render RAM/CPU spikes and OOM restarts
    """

    def __init__(self, max_concurrent: int = 10, update_interval: int = 4):
        self.max_concurrent = max_concurrent
        self.update_interval = update_interval
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._active_tasks = 0
        self._queue: List[Dict] = []
        self._lock = asyncio.Lock()
        self._updater_task: Optional[asyncio.Task] = None

    @property
    def active_count(self) -> int:
        return self._active_tasks

    @property
    def queue_length(self) -> int:
        return len(self._queue)

    async def _update_all_waiting_positions(self):
        """Periodically update the queue position on Telegram for all waiting users"""
        while True:
            await asyncio.sleep(self.update_interval)
            async with self._lock:
                if not self._queue:
                    break

                for index, item in enumerate(self._queue):
                    position = index + 1
                    status_msg = item.get("status_msg")
                    last_pos = item.get("last_pos", -1)

                    # Only edit if position changed
                    if status_msg and position != last_pos:
                        item["last_pos"] = position
                        try:
                            text = (
                                "⏳ <b>QUEUE / WAITING LINE</b> ⏳\n\n"
                                f"📍 <b>Aapka Number:</b> <code>#{position}</code>\n"
                                f"👥 <b>Active Extractions:</b> <code>{self._active_tasks}/{self.max_concurrent}</code>\n"
                                f"📋 <b>Total Waiting:</b> <code>{len(self._queue)}</code>\n\n"
                                "<i>Jaise hi aage wale users ka extraction complete hoga, aapka number automatically shuru ho jayega!</i>\n"
                                "🔄 <i>(Yeh status live update ho raha hai...)</i>"
                            )
                            # Supports pyrogram / telegram message objects
                            await status_msg.edit_text(text)
                        except Exception as e:
                            logger.debug(f"Queue message edit error: {e}")

    def _ensure_updater_running(self):
        """Start updater background task if not running"""
        if self._updater_task is None or self._updater_task.done():
            self._updater_task = asyncio.create_task(self._update_all_waiting_positions())

    async def acquire(self, chat_id: int, user_name: str = "User", status_msg=None) -> bool:
        """
        Request a slot in the extraction queue.
        If slots are free (< max_concurrent), starts immediately.
        Otherwise, waits in queue and live-updates status_msg until a slot is free.
        """
        async with self._lock:
            # If slot is immediately available
            if self._active_tasks < self.max_concurrent:
                self._active_tasks += 1
                return True

            # Otherwise, add to waiting queue
            event = asyncio.Event()
            queue_item = {
                "chat_id": chat_id,
                "user_name": user_name,
                "status_msg": status_msg,
                "event": event,
                "last_pos": len(self._queue) + 1,
                "joined_at": time.time()
            }
            self._queue.append(queue_item)
            position = len(self._queue)

            if status_msg:
                try:
                    init_text = (
                        "⏳ <b>QUEUE / WAITING LINE</b> ⏳\n\n"
                        f"📍 <b>Aapka Number:</b> <code>#{position}</code>\n"
                        f"👥 <b>Active Extractions:</b> <code>{self._active_tasks}/{self.max_concurrent}</code>\n"
                        f"📋 <b>Total Waiting:</b> <code>{len(self._queue)}</code>\n\n"
                        "<i>Server par load maintain rakhne ke liye aapko queue me rakha gaya hai. Kripya intezar karein...</i>\n"
                        "🔄 <i>(Aapka number live update hota rahega)</i>"
                    )
                    await status_msg.edit_text(init_text)
                except Exception as e:
                    logger.debug(f"Initial queue msg edit error: {e}")

            self._ensure_updater_running()

        # Wait until awakened when a slot is released
        try:
            await event.wait()
            return True
        except asyncio.CancelledError:
            async with self._lock:
                if queue_item in self._queue:
                    self._queue.remove(queue_item)
            raise

    async def release(self):
        """Release a slot and notify the next waiting user in queue"""
        async with self._lock:
            if self._queue:
                next_item = self._queue.pop(0)
                status_msg = next_item.get("status_msg")
                if status_msg:
                    try:
                        await status_msg.edit_text(
                            "🚀 <b>Aapka Number Aa Gaya Hai!</b>\n\n"
                            "🔄 <i>Extraction shuru ho raha hai, kripya intezar karein...</i>"
                        )
                    except Exception as e:
                        logger.debug(f"Slot release status update error: {e}")
                next_item["event"].set()
            else:
                self._active_tasks = max(0, self._active_tasks - 1)

    async def get_stats(self) -> Dict:
        """Get current queue & concurrency statistics"""
        async with self._lock:
            return {
                "active_tasks": self._active_tasks,
                "max_concurrent": self.max_concurrent,
                "waiting_users": len(self._queue)
            }


# Global Queue Manager instance (Default: 10 concurrent extractions)
extraction_queue = TaskQueueManager(max_concurrent=10, update_interval=4)


class QueueContext:
    """
    Context manager for effortless queue handling in any module:
    Usage:
        from Extractor.core.queue_manager import QueueContext

        async with QueueContext(chat_id=m.chat.id, user_name=m.from_user.first_name, status_msg=status_msg):
            # Your extraction logic here
            ...
    """
    def __init__(self, chat_id: int, user_name: str = "User", status_msg=None, queue_mgr: TaskQueueManager = extraction_queue):
        self.chat_id = chat_id
        self.user_name = user_name
        self.status_msg = status_msg
        self.queue_mgr = queue_mgr
        self._acquired = False

    async def __aenter__(self):
        await self.queue_mgr.acquire(
            chat_id=self.chat_id,
            user_name=self.user_name,
            status_msg=self.status_msg
        )
        self._acquired = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._acquired:
            await self.queue_mgr.release()
