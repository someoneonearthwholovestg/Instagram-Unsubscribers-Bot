import logging
from typing import Type, Union

import aiohttp

from app import MODE, MODE_LOCAL_POLLING
from data_managers import FileDataManager, EnvVarsDataManager
from telegram_bot.TelegramBotController import TelegramBotController
from telegram_bot.TelegramBotSession import TelegramBotSession
from telegram_bot.TelegramBotUpdate import TelegramBotUpdate
from telegram_bot.TelegramBotWorker import TelegramBotWorker
from utils import make_object_from_dict


class TelegramBot:

    def __init__(self, worker):
        self.worker: TelegramBotWorker = worker
        if MODE == MODE_LOCAL_POLLING:
            self.storage = FileDataManager()
        else:
            self.storage = EnvVarsDataManager()
        self.authorized_users = self.storage.get_authorised_telegram_usernames()
        self.known_sessions = set()
        self.commands = dict()
        self.last_offset = self.storage.get_telegram_bot_last_offset()
        self.permanent_callbacks = dict()
        self.default_controller = None
        self.middleware = []

    async def start_polling(self):
        assert self.default_controller is not None
        logging.info('Start polling')
        async with aiohttp.ClientSession(connector=self.worker.conn) as session:
            self.worker.session = session
            while True:
                update_request = self.worker.BASE_URL + 'getUpdates?timeout=10000&offset={}'.format(self.last_offset)
                async with session.get(update_request) as response:
                    logging.info('Received update from telegram')
                    json = await response.json()
                    if json['ok']:
                        for update_json in json['result']:
                            await self.serve_update(update_json)

    async def serve_update(self, update_json):
        self.last_offset = int(update_json['update_id']) + 1
        self.storage.set_telegram_bot_last_offset(str(self.last_offset))

        if not self._authorize(update_json):
            logging.info('Not authorised telegram user request denied')
            return

        update = make_object_from_dict(update_json, type_name='Update')
        bot_update = await self._prepare_bot_update_object(update)
        if bot_update is None:
            return

        await self._delete_old_dialogues_if_needed(bot_update)

        bot_update = self._call_middleware(bot_update)

        if bot_update.controller.requires_set_typing:
            await self.worker.set_typing(bot_update.session.chat_id)

        await self.worker.serve_controller(bot_update)

    def _authorize(self, update_json):
        if 'message' in update_json:
            return update_json['message']['from']['username'] in self.authorized_users \
                   and update_json['message']['chat']['type'] == 'private'
        if 'callback_query' in update_json:
            return update_json['callback_query']['from']['username'] in self.authorized_users \
                   and update_json['callback_query']['message']['chat']['type'] == 'private'
        return False

    async def _prepare_bot_update_object(self, update):
        callback_query = None
        message_text = None
        controller = None
        if hasattr(update, 'message'):
            chat_id = update.message.from_.id
            username = update.message.from_.username
            message_text = update.message.text
        elif hasattr(update, 'callback_query'):
            chat_id = update.callback_query.from_.id
            username = update.callback_query.from_.username
            callback_query = update.callback_query.data
        else:
            logging.warning('_prepare_bot_update_object : unknown api format from telegram')
            return None

        session = self._search_or_create_session(chat_id, username)

        if callback_query is None:
            session.answering_callback_query = None
        else:
            session.answering_callback_query = update.callback_query.id

        if callback_query:
            if session.previous_controller and session.previous_controller.callbacks and \
                    callback_query in session.previous_controller.callbacks:
                controller = session.previous_controller.callbacks[callback_query]

            elif callback_query in self.permanent_callbacks:
                controller = self.permanent_callbacks[callback_query]
            else:
                await self.worker.answer_callback_query(session.answering_callback_query)

        elif session.pending_controllers:
            controller = session.pending_controllers.pop()

        elif message_text and message_text in self.commands:
            controller = self.commands[message_text]
        else:
            controller = self.default_controller

        if controller is None or session is None or update is None:
            logging.warning('_prepare_bot_update_object : unknown api format from telegram')
            return None

        bot_update = TelegramBotUpdate(bot=self, update=update, session=session, controller=controller)
        if message_text:
            bot_update.message_text = message_text
            bot_update.message_id = update.message.message_id
        return bot_update

    def _call_middleware(self, bot_update: TelegramBotUpdate):
        for middleware in self.middleware:
            bot_update = middleware(bot_update)
        return bot_update

    def _search_or_create_session(self, chat_id, username):
        try:
            session = next(s for s in self.known_sessions if s.chat_id == chat_id)
        except StopIteration:
            session = TelegramBotSession(chat_id=chat_id,
                                         username=username)
            self.known_sessions.add(session)
        return session

    async def _delete_old_dialogues_if_needed(self, bot_update: TelegramBotUpdate):
        for message_id in bot_update.session.message_ids_to_delete:
            await self.worker.delete_message(message_id, chat_id=bot_update.session.chat_id)
        bot_update.session.message_ids_to_delete = []

    # MARK: - utils

    def set_default_controller(self, controller: Type[TelegramBotController]):
        self.default_controller = controller()
        return controller

    def add_controller(self, controller: Union[Type[TelegramBotController], TelegramBotController]):
        assert controller.command is not None
        if isinstance(controller, TelegramBotController.__class__):
            instance: TelegramBotController = controller()
        else:
            instance: TelegramBotController = controller
        command = instance.command
        if command[0] != '/':
            command = '/' + command
        assert command not in self.commands
        self.commands[command] = instance

        if instance.permanent_callbacks is not None:
            self.permanent_callbacks.update(instance.permanent_callbacks)
        return controller

    def add_controllers(self, controllers):
        for controller in controllers:
            self.add_controller(controller)

    def add_middleware(self, middleware):
        self.middleware += [middleware]
        return middleware

    def add_permanent_callbacks(self, callbacks):
        self.permanent_callbacks.update(callbacks)
