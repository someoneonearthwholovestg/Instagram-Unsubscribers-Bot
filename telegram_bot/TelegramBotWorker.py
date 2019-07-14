import logging

from aiohttp_socks import SocksConnector, SocksVer

from app import MODE, MODE_LOCAL_POLLING
from telegram_bot.TelegramBotResponse import TelegramBotResponse
from telegram_bot.TelegramBotSession import TelegramBotSession


class TelegramBotWorker:

    def __init__(self, token):
        self.token = token
        if MODE == MODE_LOCAL_POLLING:
            self.conn = SocksConnector(socks_ver=SocksVer.SOCKS5,
                                       host='orbtl.s5.opennetwork.cc',
                                       port=999,
                                       username='91945569',
                                       password='XaKz5W8c')
            # self.conn = None
        else:
            self.conn = None
        self.BASE_URL = 'https://api.telegram.org/bot{}/'.format(token)
        self.session = None

    async def serve_controller(self, bot_update):
        response = TelegramBotResponse()

        bot_update.prepare_response(response)

        await bot_update.controller.process(bot_update, response)

        await self.send_response(session=bot_update.session,
                                 response=response)
        bot_update.session.previous_controller = bot_update.controller  # проверить что в set контроллер изменился!!!

    async def send_response(self, session: TelegramBotSession, response: TelegramBotResponse):
        if session.answering_callback_query is not None:
            await self.answer_callback_query(session.answering_callback_query)
        if response.text is None:
            logging.warning('Response has no text')
            return
        args = ''

        if response.parse_mode:
            args += '&parse_mode={}'.format(response.parse_mode)
        if response.disable_web_page_preview:
            args += '&disable_web_page_preview=true'

        if response.inline_keyboard:
            inline_keyboard = '['
            needs_coma = False
            for buttons in response.inline_keyboard:
                if needs_coma:
                    inline_keyboard += ','
                needs_coma = True
                inline_keyboard += '['
                for button in buttons:
                    inline_keyboard += button.to_json()
                inline_keyboard += ']'
            inline_keyboard += ']'
            args += '&reply_markup={"inline_keyboard": %s}' % inline_keyboard

        if args == '':
            args = None
        res = await self._send_message(response.text, args=args, chat_id=session.chat_id)

        if response.is_to_be_deleted:
            json = await res.json()
            session.message_ids_to_delete += [json['result']['message_id']]

    async def _send_message(self, message, chat_id, args=None):
        if message == '':
            return
        request = self.BASE_URL + 'sendMessage?chat_id={}&text={}'.format(chat_id, message)
        if args:
            request += args
        r = await self.session.get(request)

        if r.status >= 400:
            raise Exception(r.reason)
        return r

    async def delete_message(self, message_id, chat_id):
        await self.session.get(
            self.BASE_URL + 'deleteMessage?chat_id={}&message_id={}'.format(chat_id, message_id)
        )

    async def answer_callback_query(self, query_id):
        await self.session.get(
            self.BASE_URL + 'answerCallbackQuery?callback_query_id={}'.format(query_id)
        )

    async def set_typing(self, peer):
        await self.session.get(
            self.BASE_URL + 'sendChatAction?chat_id={}&action=typing'.format(peer)
        )
