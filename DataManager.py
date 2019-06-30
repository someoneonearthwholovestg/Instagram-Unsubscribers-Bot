import configparser


class DataManager:
    def __init__(self, config_file):
        self._config_file = config_file
        self._config = configparser.ConfigParser()

    def get_known_unfollowed_list(self, USER_ID):
        self._config.read(self._config_file)
        try:
            r: str = self._config['KNOWN_UNFOLLOWED'][USER_ID]
            return set(map(lambda x: int(x), self._string_to_set(r)))
        except KeyError:
            return {}

    def set_known_unfollowed_list(self, USER_ID, unfollowed_list):
        self._config['KNOWN_UNFOLLOWED'] = {USER_ID: unfollowed_list}
        self._save()

    def set_telegram_bot_last_offset(self, offset):
        self._config['TELEGRAM']['last_offset'] = offset
        self._save()

    def get_telegram_bot_last_offset(self):
        self._config.read(self._config_file)
        try:
            r = self._config['TELEGRAM']['last_offset']
        except:
            return -1
        return r

    def _save(self):
        with open(self._config_file, 'w') as configfile:
            self._config.write(configfile)

    def get_authorised_telegram_usernames(self):
        self._config.read(self._config_file)
        try:
            r: str = self._config['TELEGRAM']['AUTHORIZED_USERS']
            return self._string_to_set(r)
        except:
            return {}

    def _string_to_set(self, string) -> set:
        return set(string.split('{')[1].split('}')[0].split(', '))