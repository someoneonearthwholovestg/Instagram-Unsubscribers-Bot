import logging

from InstagramAPI import InstagramAPI

from utils import make_object_from_dict


class InstagramClientException(Exception):
    pass


class Following:
    def __init__(self, json: dict):
        for key, value in json.items():
            setattr(self, key, make_object_from_dict(value, type_name=key))

    def __hash__(self):
        return self.pk

    def __eq__(self, other):
        return self.pk == other.pk


class InstagramClientModel:

    def __init__(self, username: str, passwd: str):
        self.api = InstagramAPI(username=username, password=passwd)
        self.followers = set()
        self.followings = set()
        self.unfollowers = set()
        self.new_unfollowers = set()
        self.unfollowers = set()
        self.old_unfollowers = set()

    def login(self, force=False) -> bool:
        return self.api.login(force)

    def update(self):
        self._update_followings()
        self._update_followers()

        self.old_unfollowers = self.unfollowers.intersection(self.followings).difference(self.followers)

        self.unfollowers = self.followings.difference(self.followers)
        self.new_unfollowers = self.unfollowers.difference(self.old_unfollowers)

    def _update_followings(self):
        followings_json = self._try_with_relogin(
            lambda: self._get_big_list_api_method(
                self.api.getUserFollowings))
        self.followings = set()
        for following_json in followings_json:
            following = Following(following_json)
            self.followings.add(following)

    def _update_followers(self):
        followers_json = self._try_with_relogin(
            lambda: self._get_big_list_api_method(
                self.api.getUserFollowers))
        self.followers = set()
        for follower_json in followers_json:
            follower = Following(follower_json)
            self.followers.add(follower)

    def _get_big_list_api_method(self, api_method: callable):
        # works with methods: getUserFollowings, getUserFollowers
        result = []
        next_max_id = ''
        while True:
            success = api_method(self.api.username_id, next_max_id)
            if not success:
                raise InstagramClientException()
            temp = self.api.LastJson

            for item in temp["users"]:
                result.append(item)

            if temp["big_list"] is False:
                return result
            next_max_id = temp["next_max_id"]

    def _try_with_relogin(self, api_method: callable):
        try:
            result = api_method()
        except InstagramClientException:
            logging.info('Attempt to relogin')
            self.api.login(force=True)
            result = lambda x: api_method(x)
        return result