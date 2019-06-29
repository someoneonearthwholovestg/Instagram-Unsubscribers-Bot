from InstagramClientModel import InstagramClientModel


class TelegramAppSession:

    def __init__(self, chat_id: str, username: str):
        self.chat_id = chat_id
        self.username = username
        self.pending_controller: callable = None
        self.instagram_client: InstagramClientModel = None
        self.message_ids_to_delete = []

    def set_pending_controller(self, pending, on_success):
        self.pending_controller = lambda x, y: pending(x, y, on_success)

    def connect_instagram(self, login, password) -> bool:
        self.instagram_client = InstagramClientModel(login, password)
        return self.instagram_client.login()

    def disconnect_instagram(self):
        self.instagram_client = None

    is_instagram_connected = property()
    @is_instagram_connected.getter
    def is_instagram_connected(self) -> bool:
        return self.instagram_client is not None