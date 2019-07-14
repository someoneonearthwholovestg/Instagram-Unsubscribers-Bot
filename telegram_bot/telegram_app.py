import os

from instagram_client.NewUnfollowersController import NewUnfollowersController, LogoutInstagramController
from instagram_client.instagram_login_middleware import instagram_login_middleware
from instagram_client.notifications_controllers import SubscribeController, ScheduledTasksManager, UnsubscribeController
from telegram_bot.TelegramBot import TelegramBot
from telegram_bot.TelegramBotWorker import TelegramBotWorker
from telegram_bot.start_controller import DefaultController, StartController, TestController

TOKEN = os.getenv('TOKEN')
worker = TelegramBotWorker(TOKEN)
app = TelegramBot(worker)
scheduler = ScheduledTasksManager(worker)

subscribe_controller = SubscribeController(scheduler)
unsubscribe_controller = UnsubscribeController(scheduler)

app.set_default_controller(DefaultController)
app.add_controllers([
    StartController,
    NewUnfollowersController,
    subscribe_controller,
    unsubscribe_controller,
    LogoutInstagramController,
    TestController,
])

app.add_permanent_callbacks({
    StartController.check_unfollowers_callback: NewUnfollowersController(),
    StartController.subscribe_callback: subscribe_controller,
    StartController.unsubscribe_callback: unsubscribe_controller,
    StartController.logout_callback: LogoutInstagramController(),
})

app.add_middleware(instagram_login_middleware)
