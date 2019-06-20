import collections
from DataManager import DataManager
from InstagramAPI import InstagramAPI


class FollowingsManager:

    def __init__(self, client_id: str, instagram_api: InstagramAPI, storage_manager: DataManager):
        self.id = client_id
        self.api = instagram_api
        self.storage = storage_manager
        self._followers = []
        self._followings = []
        self._followers_ids = []

    def get_followers(self, update: bool):
        if update:
            self._followers = self.api.getTotalFollowers(self.id)
        return self._followers

    def get_followings(self, update: bool):
        if update:
            self._followings = self.api.getTotalFollowings(self.id)
        return self._followings

    def get_unfollowers(self, update: bool, ids=False) -> collections.Iterable:
        followers = self.get_followers(update)
        followings = self.get_followings(update)
        if update:
            self._followers_ids = set(map(lambda f: f['pk'], followers))
        unfollowed = []

        for following in followings:
            following_id = following['pk']
            if following_id not in self._followers_ids:
                unfollowed += [following['pk'] if ids else following]
        return unfollowed

    def get_old_unfollowers_ids(self) -> collections.Iterable:
        return self.storage.get_known_unfollowed_list(self.id)

    def get_new_unfollowers(self, update: bool) -> collections.Iterable:
        all_unfollowers = self.get_unfollowers(ids=False, update=update)
        all_unfollowers_ids = set(map(lambda x: x['pk'], all_unfollowers))
        old_unfollowers_ids = self.get_old_unfollowers_ids()
        new_unfollowers_ids = set()
        for unfollower_id in all_unfollowers_ids:
            if not unfollower_id in old_unfollowers_ids:
                new_unfollowers_ids.add(unfollower_id)
        self._set_old_unfollowers_ids(all_unfollowers_ids)
        new_unfollowers = []
        for unfollower_id in new_unfollowers_ids:
            new_unfollowers += [next(x for x in all_unfollowers if x['pk'] == unfollower_id)]
        return new_unfollowers

    def login(self, force=False):
        self.api.login(force)

    def _set_old_unfollowers_ids(self, ids):
        self.storage.set_known_unfollowed_list(self.id, unfollowed_list=ids)