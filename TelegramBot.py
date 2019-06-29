import aiohttp
from aiohttp_socks import SocksConnector, SocksVer
from collections import namedtuple
import keyword

from DataManager import DataManager
from TelegramAppSession import TelegramAppSession
from TelegramBotResponse import TelegramBotResponse


class TelegramBot:

    def __init__(self, token: str, commands: dict, callbacks: dict):
        self.token = token
        self.storage = DataManager('config.ini')
        conn = SocksConnector(socks_ver=SocksVer.SOCKS5,
                              host='orbtl.s5.opennetwork.cc',
                              port='999',
                              username='91945569',
                              password='XaKz5W8c')
        self.session = aiohttp.ClientSession(connector=conn)
        self.BASE_URL = 'https://api.telegram.org/bot{}/'.format(token)
        self.authorized_users = self.storage.get_authorised_telegram_usernames()
        self.known_sessions = set()
        self.commands = commands
        self.callbacks = callbacks
        self.last_offset = self.storage.get_telegram_bot_last_offset()

    async def start_responding(self):
        while True:
            update_request = self.BASE_URL + 'getUpdates?timeout=10000&offset={}'.format(self.last_offset)
            try:
                response: aiohttp.ClientResponse = await self.session.get(update_request)
                json = await response.json()
                if json['ok']:
                    await self._dispatch(json['result'])
                else:
                    raise Exception('json not ok...')
            except Exception as e:
                await self.session.close()
                raise e

    async def _dispatch(self, results):
        for update in results:
            self.last_offset = int(update['update_id']) + 1
            self.storage.set_telegram_bot_last_offset(str(self.last_offset))

            if not self._authorize(update):
                return
            update = self._make_object_from_dict(update, type_name='Update')
            session, controller, chat_id = self._get_session_and_controller_and_chat_id(update)
            if session is None:
                print('something very bad happened: session cant be created')
                return

            if session.pending_controller is not None:
                pending_controller = session.pending_controller
                session.pending_controller = None
                bot_response = await pending_controller(session, update)
                pass
            elif controller is None:
                return
            else:
                bot_response = await controller(session, update)
                pass

            if issubclass(type(bot_response), TelegramBotResponse):
                await self._handle_response(session=session, response=bot_response)
            elif type(bot_response) is str:
                await self.send_message(bot_response, chat_id=chat_id)

    def _get_session_and_controller_and_chat_id(self, update) -> (TelegramAppSession, callable, str):
        session = None
        controller = None
        chat_id = None
        if hasattr(update, 'message'):
            chat_id = update.message.from_.id
            session = self._find_or_create_session(chat_id, update.message.from_.username)
            command = update.message.text
            if command in self.commands:
                controller = self.commands[command]
            else:
                controller = self.commands['default']
        elif hasattr(update, 'callback_query'):
            chat_id = update.callback_query.from_.id
            session = self._find_or_create_session(chat_id, update.callback_query.from_.username)
            command = update.callback_query.data
            chat_id = update.callback_query.from_.id
            if command in self.callbacks:
                controller = self.callbacks[command]

        return session, controller, chat_id

    def _find_or_create_session(self, chat_id, username):
        try:
            session = next(s for s in self.known_sessions if s.chat_id == chat_id)
        except StopIteration:
            session = TelegramAppSession(chat_id=chat_id,
                                         username=username)
            self.known_sessions.add(session)
        return session

    async def _handle_response(self, session: TelegramAppSession, response: TelegramBotResponse):
        args = ''

        if response.flush_delete_messages:
            for message_id in session.message_ids_to_delete:
                await self.delete_message(message_id, session.chat_id)
            session.message_ids_to_delete = []

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
        res = await self.send_message(response.text, args=args, chat_id=session.chat_id)
        if response.is_to_be_deleted:
            json = await res.json()
            session.message_ids_to_delete += [json['result']['message_id']]

    def _authorize(self, update):
        if 'message' in update:
            return update['message']['from']['username'] in self.authorized_users \
                   and update['message']['chat']['type'] == 'private'
        if 'callback_query' in update:
            return update['callback_query']['from']['username'] in self.authorized_users \
                   and update['callback_query']['message']['chat']['type'] == 'private'
        return False

    def _make_object_from_dict(self, update_dict: dict, type_name: str):
        for k, v in update_dict.items():
            if issubclass(dict, type(v)):
                update_dict[k] = self._make_object_from_dict(v, type_name=str(k))

        field_names = list(map(lambda x: x + '_' if keyword.iskeyword(x) else x, update_dict.keys()))
        if keyword.iskeyword(type_name):
            type_name = type_name + '_'
        return namedtuple(type_name, field_names)(*update_dict.values())

    async def send_message(self, message, chat_id, args=None,):
        request = self.BASE_URL + 'sendMessage?chat_id={}&text={}'.format(chat_id, message)
        if args:
            request += args
        r = await self.session.get(request)

        if r.status >= 400:
            raise Exception(r.reason)
        return r

    async def delete_message(self, message_id, chat_id):
        r = await self.session.get(
            self.BASE_URL + 'deleteMessage?chat_id={}&message_id={}'.format(chat_id, message_id)
        )
        if r.status >= 400:
            raise Exception(r.reason)