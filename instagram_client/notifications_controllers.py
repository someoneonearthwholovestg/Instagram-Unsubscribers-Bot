import asyncio
from time import time

from telegram_bot.TelegramBotResponse import TelegramBotResponse
from telegram_bot.TelegramBotUpdate import TelegramBotUpdate
from .NewUnfollowersController import NewUnfollowersController, InstagramApiController


class ScheduledTasksManager:

    def __init__(self, worker):
        self.subscribed_sessions = set()
        self.controller = NewUnfollowersController()
        self.worker = worker

    async def start(self, interval=60 * 60):
        while True:
            t_start = time()
            for session in self.subscribed_sessions:
                bot_update = TelegramBotUpdate(bot=None,
                                               update=None,
                                               session=session,
                                               controller=self.controller)
                await self.worker.serve_controller(bot_update)

            time_executed = time() - t_start
            rest = interval - time_executed
            rest = rest if rest > 0 else interval
            await asyncio.sleep(rest)


class SubscribeController(InstagramApiController):
    command = 'start_notifying'

    def __init__(self, task_manager):
        self.tasks_manager: ScheduledTasksManager = task_manager

    async def process(self, bot_update, response: TelegramBotResponse):
        self.tasks_manager.subscribed_sessions.add(bot_update.session)
        response.text = 'Now you will be notified in 24 hours after someone unfollowing you!'


class UnsubscribeController(InstagramApiController):
    requires_instagram_connection = False
    command = 'stop_notifying'

    def __init__(self, task_manager):
        self.tasks_manager: ScheduledTasksManager = task_manager

    async def process(self, bot_update, response: TelegramBotResponse):
        if bot_update.session in self.tasks_manager.subscribed_sessions:
            self.tasks_manager.subscribed_sessions.remove(bot_update.session)
        response.text = "Now you won't be notified if someone unfollowing you!"
