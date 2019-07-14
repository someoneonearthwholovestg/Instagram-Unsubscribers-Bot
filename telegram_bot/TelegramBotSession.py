from time import time

from instagram_client.InstagramClientModel import InstagramClientModel


class TelegramBotSession:

    def __init__(self, chat_id: str, username: str):
        self.chat_id = chat_id
        self.username = username
        self.pending_controllers = []
        self.instagram_client: InstagramClientModel = None
        self.message_ids_to_delete = []
        self.answering_callback_query = None

        self.previous_controller = None

        self.time_instagram_connected = None

    def connect_instagram(self, login, password) -> bool:
        self.instagram_client = InstagramClientModel(login, password)
        success = self.instagram_client.login()
        if success:
            self.time_instagram_connected = time()
        return success

    def disconnect_instagram(self):
        self.instagram_client = None
        self.time_instagram_connected = None

    is_instagram_connected = property()
    @is_instagram_connected.getter
    def is_instagram_connected(self) -> bool:
        return self.instagram_client is not None and self.instagram_client.api.isLoggedIn