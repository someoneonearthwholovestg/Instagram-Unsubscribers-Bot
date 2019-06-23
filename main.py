from InstagramAPI import InstagramAPI
import asyncio

from DataManager import DataManager
from FollowingsModel import FollowingsModel
from TelegramController import TelegramController


async def periodic_unsubs_check_task():
    SECONDS_TO_WAIT = 60 * 60 * 60
    while True:
        await telegram_controller.new_unsubs(username='fightLikeABrave', only_new_unsubs=True)
        await asyncio.sleep(SECONDS_TO_WAIT)

if __name__ == '__main__':
    TOKEN = '672100742:AAEj-1j0E-BMjOW6nyuuha6DGpgifIY_EBc'
    data_manager = DataManager('config.ini')
    credentials = data_manager.get_user_credentials()
    api = InstagramAPI(credentials['username'], credentials['password'])
    user_id = credentials['id']
    followings_model = FollowingsModel(user_id, api, data_manager)
    telegram_controller = TelegramController(TOKEN, followings_model=followings_model)

    api.login(True)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait([
        periodic_unsubs_check_task(),
        telegram_controller.start_responding(),
    ]))
