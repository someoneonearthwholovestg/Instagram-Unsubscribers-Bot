import configparser
from abc import ABC
import os
import logging


class DataManagerProtocol(ABC):

    def set_telegram_bot_last_offset(self, offset):
        pass

    def get_telegram_bot_last_offset(self):
        pass

    def get_authorised_telegram_usernames(self):
        pass


def _string_to_set(string) -> set:
    return set(string.split('{')[1].split('}')[0].split(', '))


class FileDataManager(DataManagerProtocol):
    # data is based in config file
    def __init__(self, config_file=None):
        if config_file is None:
            config_file = 'config.ini'
        self._config_file = config_file
        self._config = configparser.ConfigParser()

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
            return _string_to_set(r)
        except:
            return {}


class EnvVarsDataManager(DataManagerProtocol):
    def get_telegram_bot_last_offset(self):
        return os.getenv('TELEGRAM_BOT_LAST_OFFSET', -1)

    def set_telegram_bot_last_offset(self, offset):
        os.putenv('TELEGRAM_BOT_LAST_OFFSET', offset)

    def get_authorised_telegram_usernames(self):
        envvar = os.getenv('AUTHORISED_TELEGRAM_USERNAMES')
        if envvar is None:
            logging.error('No AUTHORISED_TELEGRAM_USERNAMES environmental var')
        return _string_to_set(envvar)