class TelegramBotResponse:

    PARSE_MODE_MARKDOWN = 'Markdown'

    def __init__(self, text: str = None):
        self.text = text
        self.inline_keyboard = None
        self.flush_delete_messages = False
        self.is_to_be_deleted = False
        self.parse_mode = None
        self.disable_web_page_preview = True

class InlineKeyboardButton:

    def __init__(self, text, callback_data=None):
        self.text = text
        self.callback_data = callback_data

    def to_json(self) -> str:
        res = '"text": "{}", "callback_data": "{}"'.format(self.text, self.callback_data)
        return '{' + res + '}'