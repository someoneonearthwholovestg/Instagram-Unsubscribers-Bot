from time import time

from telegram_bot.TelegramBotController import TelegramBotController
from telegram_bot.TelegramBotResponse import InlineKeyboardButton, TelegramBotResponse


class StartController(TelegramBotController):
    check_unfollowers_callback = 'check'
    subscribe_callback = 'subscribe'
    unsubscribe_callback = 'unsubscribe'
    logout_callback = 'logout'

    command = 'start'
    delete_dialogue_after = False

    default_inline_keyboard = [
        [InlineKeyboardButton(text='Check who unfollowed me', callback_data=check_unfollowers_callback), ],
        [InlineKeyboardButton(text='Notify me if i was unfollowed', callback_data=subscribe_callback), ],
        [InlineKeyboardButton(text='Stop notifying me', callback_data=unsubscribe_callback), ],
        [InlineKeyboardButton(text='Logout from my Instagram', callback_data=logout_callback), ],
    ]

    async def process(self, bot_update, response):
        response.text = \
            '''Hello!\n
            • I can manually check, who unfollowed you in Instagram.
            • I can notify you if somebody unfollowed you, if you want.
            • I don't store your Instagram password :)\n
            • Please, try to break me down, because it's alpha release. If you do, notify @fightLikeABrave
            '''


class DefaultController(TelegramBotController):
    command = ''
    delete_dialogue_after = True

    async def process(self, bot_update, response):
        response.text = 'No such a command, use /start to get help'


class TestController(TelegramBotController):
    command = 'status'
    delete_dialogue_after = False

    async def process(self, bot_update, response: TelegramBotResponse):
        if bot_update.session.instagram_client is None:
            message = 'session.instagram_client is None'
        elif not bot_update.session.instagram_client.api.isLoggedIn:
            message = 'session.instagram_client.api.isLoggedIn is False. Relogin?'
        else:
            message = 'session.instagram_client.api.isLoggedIn is True. Performing check request to api.\n'
            bot_update.session.instagram_client.api.getProfileData()
            r = bot_update.session.instagram_client.api.LastResponse
            message += 'response status code: {}'.format(r.status_code)

        if bot_update.session.time_instagram_connected:
            message += '\n time instagram connected (seconds): {}' \
                .format(int(time() - bot_update.session.time_instagram_connected))
        response.text = message
