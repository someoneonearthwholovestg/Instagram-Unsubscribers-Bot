import collections
from InstagramAPI import InstagramAPI


class InstagramClientModel:

    def __init__(self, username: str, passwd: str):
        self.api = InstagramAPI(username=username, password=passwd)
        self._followers = []
        self._followings = []
        self._unfollowers = []
        self._new_unfollowers = []

    def get_followers(self, update=True):
        if update:
            # self._followers = self.api.getTotalFollowers(self.api.username_id)
            self._followers = self._try_request_with_relogin(self.api.getTotalFollowers)
        return self._followers

    def get_followings(self, update=True):
        if update:
            self._followings = self._try_request_with_relogin(self.api.getTotalFollowings)
            # self._followings = self.api.getTotalFollowings(self.api.username_id)
        return self._followings

    def get_unfollowers(self, update=True) -> collections.Iterable:
        if update:
            followers = self.get_followers(update)
            followings = self.get_followings(update)
            followers_ids = set(map(lambda f: f['pk'], followers))
            unfollowers = list(filter(lambda f: f['pk'] not in followers_ids, followings))
            self._unfollowers = unfollowers
        return self._unfollowers

    def get_new_unfollowers(self, update=True) -> collections.Iterable:
        if update:
            old_unfollowers_ids = self._unfollowers
            all_unfollowers_ids = self.get_unfollowers(update=update)
            new_unfollowers_ids = filter(lambda f: f not in all_unfollowers_ids, old_unfollowers_ids)
            self._new_unfollowers = [next(f for f in all_unfollowers_ids if f['pk'] == id) for id in new_unfollowers_ids]
        return self._new_unfollowers

    def login(self, force=False):
        return self.api.login(force)

    def _try_request_with_relogin(self, method: callable):
        try:
            result = method(self.api.username_id)
        except Exception as e:
            #TODO: придумать как это тестировать потому что эта пушка выстрелит когда-нибудь
            print(e)
            print('\nattempt to relogin\n')
            self.api.login(force=True)
            result = method(self.api.username_id)
        return result
