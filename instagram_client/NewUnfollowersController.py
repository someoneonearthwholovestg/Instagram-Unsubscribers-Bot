from abc import ABC

from telegram_bot.TelegramBot import TelegramBotController
from telegram_bot.TelegramBotResponse import TelegramBotResponse


class InstagramApiController(TelegramBotController, ABC):

    @property
    def requires_instagram_connection(self):
        return True


class NewUnfollowersController(InstagramApiController):
    requires_set_typing = True
    command = 'new_unfollowers'
    delete_dialogue_after = False
    default_parse_mode = TelegramBotResponse.PARSE_MODE_MARKDOWN

    async def process(self, bot_update, response: TelegramBotResponse):
        instagram_client = bot_update.session.instagram_client
        instagram_client.update()

        new_unfollowers_str = ''
        for follower in instagram_client.new_unfollowers:
            new_unfollowers_str += '[{}](https://instagram.com/{})'.format(follower.username, follower.username) + '\n'
        old_unfollowers_str = ''
        for follower in instagram_client.old_unfollowers:
            old_unfollowers_str += '[{}](https://instagram.com/{})'.format(follower.username, follower.username) + '\n'

        if old_unfollowers_str != '':
            old_unfollowers_str = '\nold unfollowers:\n' + old_unfollowers_str
        if new_unfollowers_str != '':
            new_unfollowers_str = 'new unfollowers:\n' + new_unfollowers_str

        response.text = new_unfollowers_str + old_unfollowers_str


class LogoutInstagramController(InstagramApiController):
    command = 'logout_instagram'
    requires_instagram_connection = False

    async def process(self, bot_update, response: TelegramBotResponse):
        if bot_update.session.instagram_client is None:
            message = "You haven't mentioned your Instagram account"
        else:
            bot_update.session.disconnect_instagram()
            message = 'Your Instagram account is forgotten now.'
        response.text = message
