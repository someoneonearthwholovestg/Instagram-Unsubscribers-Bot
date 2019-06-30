from time import time
import asyncio

from TelegramBot import TelegramBot
from TelegramAppSession import TelegramAppSession
from TelegramBotResponse import TelegramBotResponse, InlineKeyboardButton


class TelegramApp:

    check_unfollowers_callback = 'check'
    subscribe_callback = 'subscribe'
    unsubscribe_callback = 'unsubscribe'
    logout_callback = 'logout'

    def __init__(self, token: str):
        commands = {
            '/start': self.start_controller,
            '/new_unfollowers': self.new_unfollowers_controller,
            '/start_notifying': self.start_notifying_controller,
            '/stop_notifying': self.stop_notifying_controller,
            '/logout_instagram': self.logout_instagram_controller,
            '/help': self.start_controller,
            'default': self.default_controller,
        }
        callbacks = {
            self.check_unfollowers_callback: self.new_unfollowers_controller,
            self.subscribe_callback: self.start_notifying_controller,
            self.unsubscribe_callback: self.stop_notifying_controller,
            self.logout_callback: self.logout_instagram_controller,
        }
        self.bot = TelegramBot(token, commands, callbacks)
        self.subscribed_sessions = set()

    async def start_polling(self):
        await self.bot.start_polling()

    async def start_webhook(self, url, listen, port):
        pass

    async def start_schedule_tasks(self):
        DAY = 24 * 60 * 60
        while True:
            t_start = time()
            for session in self.subscribed_sessions:
                message = self._list_unsubs(session)
                await self.bot.send_message(message, session.chat_id)
            time_executed = time() - t_start
            rest = DAY - time_executed
            rest = rest if rest > 0 else DAY
            await asyncio.sleep(rest)

    async def start_controller(self, session, update):
        response = TelegramBotResponse('''
Hello!\n
• I can manually check, who unfollowed you in Instagram.
• I can notify you if somebody unfollowed you, if you want.
• I don't store your Instagram password :)\n
• Please, try to break me down, because it's alpha release. If you do, notify @fightLikeABrave
''')
        response.inline_keyboard = [
            [InlineKeyboardButton(text='Check who unfollowed me', callback_data=self.check_unfollowers_callback),],
            [InlineKeyboardButton(text='Notify me if i was unfollowed', callback_data=self.subscribe_callback),],
            [InlineKeyboardButton(text='Stop notifying me', callback_data=self.unsubscribe_callback),],
            [InlineKeyboardButton(text='Logout from my Instagram', callback_data=self.logout_callback),],
        ]
        return response


    async def new_unfollowers_controller(self, session: TelegramAppSession, update):
        message = self._list_unsubs(session, on_success=self.new_unfollowers_controller)
        if hasattr(update, 'message'):
            session.message_ids_to_delete += [update.message.message_id]
        res = TelegramBotResponse(message)
        res.parse_mode = res.PARSE_MODE_MARKDOWN
        return res

    def _list_unsubs(self, session, on_success=None):
        if not session.is_instagram_connected:
            return self._request_connect_instagram(session, on_success=on_success)
        instagram_client = session.instagram_client
        new_unfollowers = list(map(lambda x: x['username'], instagram_client.get_new_unfollowers(update=True)))
        unfollowers = map(lambda x: x['username'], instagram_client.get_unfollowers(update=False))

        new_unfollowers_str = ''
        for entry in new_unfollowers:
            new_unfollowers_str += '[{}](https://instagram.com/{})'.format(entry, entry) + '\n'
        all_unfollowers_str = ''
        for entry in unfollowers:
            all_unfollowers_str += '[{}](https://instagram.com/{})'.format(entry, entry) + '\n'
        return 'new unfollowers:\n' + new_unfollowers_str + '\nall unfollowers:\n' + all_unfollowers_str

    def _request_connect_instagram(self, session: TelegramAppSession, update=None, on_success=None):
        if update:
            res = self._forget_this_message_and_response(session, update)
        else:
            res = TelegramBotResponse()
        session.set_pending_controller(self.connect_instagram_controller, on_success=on_success)
        res.text = 'Enter your Instagram login and password divided by single space'
        res.is_to_be_deleted = True
        return res

    async def connect_instagram_controller(self, session, update, on_success_controller: callable = None):
        res = self._forget_this_message_and_response(session, update)
        try:
            login, password = update.message.text.split(' ')[0:2]
        except:
            res.text = 'Incorrect login/password :('
            return res

        if session.connect_instagram(login, password):
            if on_success_controller:
                result = await on_success_controller(session, update)
                text = result.text if type(result) is TelegramBotResponse else result
            else:
                text = 'Successfully logged in!'
        else:
            text = 'Incorrect login/password :('
        res.text = text
        res.flush_delete_messages = True
        res.parse_mode = TelegramBotResponse.PARSE_MODE_MARKDOWN
        return res

    async def start_notifying_controller(self, session, update):
        if not session.is_instagram_connected:
            return self._request_connect_instagram(session, on_success=self.start_notifying_controller)
        res = self._forget_this_message_and_response(session, update)
        self.subscribed_sessions.add(session)
        res.text = 'Now you will be notified in 24 hours after someone unfollows you!'
        return res

    async def stop_notifying_controller(self, session, update):
        res = self._forget_this_message_and_response(session, update)
        if session in self.subscribed_sessions:
            self.subscribed_sessions.remove(session)
        res.text = "Now you won't be notified if someone unfollows you!"
        return res

    async def logout_instagram_controller(self, session: TelegramAppSession, update):
        res = self._forget_this_message_and_response(session, update)

        if session.instagram_client is None:
            message = "You haven't mentioned your Instagram account"
        else:
            session.disconnect_instagram()
            message = 'Your Instagram account is forgotten now.'
        res.text = message
        return res

    async def default_controller(self, session, update):
        return 'No such a command, use /start to get help'

    @staticmethod
    def _forget_this_message_and_response(session, update) -> TelegramBotResponse:
        if hasattr(update, 'message'):
            session.message_ids_to_delete += [update.message.message_id]
        res = TelegramBotResponse()
        res.is_to_be_deleted = True
        return res