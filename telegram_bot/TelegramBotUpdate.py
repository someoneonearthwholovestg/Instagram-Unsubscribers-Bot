from telegram_bot.TelegramBotController import TelegramBotController
from telegram_bot.TelegramBotResponse import TelegramBotResponse
from telegram_bot.TelegramBotSession import TelegramBotSession


class TelegramBotUpdate:

    def __init__(self, bot, update, session, controller):
        self.update = update
        self.session: TelegramBotSession = session
        self.controller: TelegramBotController = controller
        self.bot = bot
        self.message_id = None
        self.message_text = None

    def prepare_response(self, response: TelegramBotResponse):
        response.parse_mode = self.controller.default_parse_mode
        response.is_to_be_deleted = self.controller.delete_dialogue_after
        response.disable_web_page_preview = self.controller.default_disable_web_page_preview
        response.inline_keyboard = self.controller.default_inline_keyboard

        if self.controller.delete_dialogue_after:
            if self.message_id:
                self.session.message_ids_to_delete += [self.message_id]

    async def activate_next_controller(self, response):
        if not self.session.pending_controllers:
            return None
        self.session.previous_controller = self.controller
        self.controller = self.session.pending_controllers.pop()
        self.prepare_response(response)
        await self.controller.process(bot_update=self, response=response)
