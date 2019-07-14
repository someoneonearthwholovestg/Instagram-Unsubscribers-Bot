from instagram_client.NewUnfollowersController import InstagramApiController
from telegram_bot.TelegramBot import TelegramBotUpdate, TelegramBotController
from telegram_bot.TelegramBotResponse import TelegramBotResponse


def instagram_login_middleware(bot_update: TelegramBotUpdate):
    if issubclass(type(bot_update.controller), InstagramApiController):
        controller: InstagramApiController = bot_update.controller
        if controller.requires_instagram_connection:
            if bot_update.session.instagram_client is None:
                bot_update.session.pending_controllers += [bot_update.controller]
                bot_update.controller = InstagramAuthAskController()
            else:
                bot_update.session.instagram_client.login()
    return bot_update


class InstagramAuthAskController(TelegramBotController):
    delete_dialogue_after = True

    async def process(self, bot_update, response: TelegramBotResponse):
        response.text = 'Enter your Instagram login and password divided by single space'
        bot_update.session.pending_controllers += [InstagramAuthCheckController()]


class InstagramAuthCheckController(TelegramBotController):
    delete_dialogue_after = True
    requires_set_typing = True

    async def process(self, bot_update: TelegramBotUpdate, res: TelegramBotResponse):
        await bot_update.bot.worker.delete_message(message_id=bot_update.message_id,
                                                   chat_id=bot_update.session.chat_id)
        try:
            login, password = bot_update.message_text.split(' ')[0:2]
        except:
            res.text = 'Incorrect login/password :('
            return
        if bot_update.session.connect_instagram(login, password):
            if bot_update.session.pending_controllers:
                await bot_update.activate_next_controller(response=res)
            else:
                res.text = 'Successfully logged in!'
        else:
            res.text = 'Incorrect login/password :('
