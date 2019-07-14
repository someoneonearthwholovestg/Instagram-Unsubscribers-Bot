from abc import ABC, abstractmethod
from typing import Optional

from telegram_bot.TelegramBotResponse import TelegramBotResponse


class TelegramBotController(ABC):

    @property
    def requires_set_typing(self):
        return False

    @property
    def default_inline_keyboard(self):
        return None

    @property
    def default_disable_web_page_preview(self):
        return True

    @property
    def default_parse_mode(self):
        return None

    @property
    def callbacks(self):
        return None

    @property
    def command(self) -> Optional[str]:
        return None

    @property
    def permanent_callbacks(self) -> Optional[dict]:
        return None

    # if True the request command and response from this controller are to be deleted
    @property
    def delete_dialogue_after(self):
        return True

    @abstractmethod
    async def process(self, bot_update, response: TelegramBotResponse):
        pass
