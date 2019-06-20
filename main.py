from InstagramAPI import InstagramAPI
import asyncio

from DataManager import DataManager
from FollowingsManager import FollowingsManager


def check_unsubs():
    USER_ID = '231279054'
    credentials = data_manager.get_user_credentials()
    api = InstagramAPI(credentials['username'], credentials['password'])
    followings_manager = FollowingsManager(USER_ID, api, data_manager)
    followings_manager.login()
    new_unfollowers = map(lambda x: x['username'], followings_manager.get_new_unfollowers(update=True))
    new_unfollowers_str = ''
    for entry in new_unfollowers:
        new_unfollowers_str += entry + '\n'
    unfollowers = map(lambda x: x['username'], followings_manager.get_unfollowers(update=False))
    unfollowers_str = ''
    for entry in unfollowers:
        unfollowers_str += entry + '\n'
    return 'new unsubs:\n' + new_unfollowers_str + '\nall unsubs:\n' + unfollowers_str

data_manager = DataManager('config.ini')

if __name__ == '__main__':
    from TelegramBot import TelegramBot

    TOKEN = '672100742:AAEj-1j0E-BMjOW6nyuuha6DGpgifIY_EBc'
    loop = asyncio.get_event_loop()
    bot = TelegramBot(TOKEN, data_manager)
    loop.run_until_complete(bot.run())
