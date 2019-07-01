import collections
from InstagramAPI import InstagramAPI
import logging


class InstagramClientException(Exception):
    pass

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
            self._followers = self._try_request_with_relogin(lambda: self._get_total_followers(self.api.username_id))
        return self._followers

    def get_followings(self, update=True):
        if update:
            self._followings = self._try_request_with_relogin(lambda: self._get_total_followings(self.api.username_id))
        return self._followings

    def get_unfollowers(self, update=True, update_old=True) -> collections.Iterable:
        # update_old is necessary if someone started following you back again
        followers = None
        if update_old:
            old_unfollowers = self._unfollowers
            followers = self.get_followers(True)
            new_unfollowers = []
            for old in old_unfollowers:
                try:
                    next(filter(lambda f: f['pk'] == old['pk'], followers))
                except StopIteration:
                    new_unfollowers += [old]
            self._unfollowers = new_unfollowers
        if update:
            if followers is None:
                followers = self.get_followers(update)
            followings = self.get_followings(update)
            followers_ids = set(map(lambda f: f['pk'], followers))
            unfollowers = list(filter(lambda f: f['pk'] not in followers_ids, followings))
            self._unfollowers = unfollowers
        return self._unfollowers

    def get_new_unfollowers(self, update=True, update_old=True) -> collections.Iterable:
        if update:
            old_unfollowers = self._unfollowers
            all_unfollowers = self.get_unfollowers(update=update, update_old=update_old)
            self._new_unfollowers = []
            for unfollower in all_unfollowers:
                try:
                    next(filter(lambda old: old['pk'] == unfollower['pk'], old_unfollowers))
                except StopIteration:
                    self._new_unfollowers += [unfollower]
        return self._new_unfollowers

    def login(self, force=False):
        return self.api.login(force)

    def _try_request_with_relogin(self, method: callable):
        try:
            result = method()
        except InstagramClientException:
            logging.info('Attempt to relogin')
            self.api.login(force=True)
            result = method()
        return result

    def _get_total_followers(self, username_id):
        followers = []
        next_max_id = ''
        while 1:
            succeeded = self.api.getUserFollowers(username_id, next_max_id)
            if not succeeded:
                raise InstagramClientException()
            temp = self.api.LastJson

            for item in temp["users"]:
                followers.append(item)

            if temp["big_list"] is False:
                return followers
            next_max_id = temp["next_max_id"]

    def _get_total_followings(self, username_id):
        followers = []
        next_max_id = ''
        while True:
            success = self.api.getUserFollowings(username_id, next_max_id)
            if not success:
                raise InstagramClientException()
            temp = self.api.LastJson

            for item in temp["users"]:
                followers.append(item)

            if temp["big_list"] is False:
                return followers
            next_max_id = temp["next_max_id"]
