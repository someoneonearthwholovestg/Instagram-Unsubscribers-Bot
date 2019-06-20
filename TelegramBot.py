import aiohttp
from collections import namedtuple
import keyword

from DataManager import DataManager
from main import check_unsubs


class TelegramBot:

    def __init__(self, token, data_manager: DataManager):
        self.token = token
        self.session = aiohttp.ClientSession()
        self.BASE_URL = 'https://api.telegram.org/bot{}/'.format(token)
        self.data_manager = data_manager
        self.authorized_users = data_manager.get_authorised_telegram_usernames()
        self.commands = {'/start': self.start_command,
                         '/new_unsubs': self.new_unsubs}
        self.last_offset = -1
        print('TelegramBot is ready')

    async def run(self):
        while True:
            try:
                response: aiohttp.ClientResponse = await self.session.get(self.BASE_URL +
                                                                          'getUpdates?timeout=10000&offset={}'
                                                                          .format(self.last_offset))
                json = await response.json()
                if json['ok']:
                    await self._dispatch(json['result'])
                else:
                    raise Exception('json not ok...')
            except Exception as e:
                print(e)
                print(type(e))
                await self.session.close()
                break

    async def _dispatch(self, results):
        for update in results:
            self.last_offset = int(update['update_id']) + 1
            if not self._authorize(update):
                return
            update = self._make_object_from_dict(update, type_name='Update')
            command = update.message.text
            try:
                await self.commands[command](update)
            except KeyError:
                return

    def _authorize(self, update):
        return update['message']['from']['username'] in self.authorized_users and update['message']['chat']['type'] == 'private'

    def _make_object_from_dict(self, update_dict: dict, type_name: str):
        for k, v in update_dict.items():
            if issubclass(dict, type(v)):
                update_dict[k] = self._make_object_from_dict(v, type_name=str(k))

        field_names = list(map(lambda x: x + '_' if keyword.iskeyword(x) else x, update_dict.keys()))
        if keyword.iskeyword(type_name):
            type_name = type_name + '_'
        return namedtuple(type_name, field_names)(*update_dict.values())

    async def _send_message(self, update, message):
        r = await self.session.get(
            self.BASE_URL + 'sendMessage?chat_id={}&text={}'.format(update.message.chat.id, message))
        if r.status >= 400:
            raise Exception(r.reason)


    async def start_command(self, update):
        await self._send_message(update, 'hello, world')

    async def new_unsubs(self, update):
        message = check_unsubs()
        await self._send_message(update, message)


