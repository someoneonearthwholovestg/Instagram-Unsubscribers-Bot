import aiohttp
from collections import namedtuple
import keyword

from FollowingsModel import FollowingsModel


class TelegramController:

    def __init__(self, token, followings_model: FollowingsModel):
        self.token = token
        self.session = aiohttp.ClientSession()
        self.BASE_URL = 'https://api.telegram.org/bot{}/'.format(token)
        self.authorized_users = followings_model.get_authorised_telegram_usernames()
        self.known_chat_ids = dict()
        self.followings_model = followings_model
        self.commands = {'/start': self.start_command,
                         '/new_unsubs': self.new_unsubs}
        self.last_offset = -1

    async def start_responding(self):
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
            chat_id = update.message.chat.id
            # TODO: переделать чтобы это хранилось в бд
            self.known_chat_ids[update.message.from_.username] = chat_id
            try:
                await self.commands[command](update=update)
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

    async def _send_message(self, message, **kwargs):
        if 'update' in kwargs:
            chat_id = kwargs['update'].message.chat.id
        elif 'chat_id' in kwargs:
            chat_id = kwargs['chat_id']
        elif 'username' in kwargs and kwargs['username'] in self.known_chat_ids:
            chat_id = self.known_chat_ids[kwargs['username']]
        else:
            #TODO: сделать по-человечески
            print('Chat id is not specified: do nothing')
            return

        r = await self.session.get(
            self.BASE_URL + 'sendMessage?chat_id={}&text={}'.format(chat_id, message))
        if r.status >= 400:
            raise Exception(r.reason)


    async def start_command(self, update):
        await self._send_message('hello, world', update=update)

    async def new_unsubs(self, **update):
        self.followings_model.login()
        new_unfollowers = list(map(lambda x: x['username'], self.followings_model.get_new_unfollowers(update=True)))
        unfollowers = map(lambda x: x['username'], self.followings_model.get_unfollowers(update=False))

        #TODO: разбить на две функции
        if len(new_unfollowers) == 0 and'only_new_unsubs' in update and update['only_new_unsubs'] == True:
            return

        new_unfollowers_str = ''
        for entry in new_unfollowers:
            new_unfollowers_str += entry + '\n'
        all_unfollowers_str = ''
        for entry in unfollowers:
            all_unfollowers_str += entry + '\n'
        message =  'new unsubs:\n' + new_unfollowers_str + '\nall unsubs:\n' + all_unfollowers_str
        await self._send_message(message, **update)
