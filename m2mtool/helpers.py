import logging
import os

import dbus
import requests

from m2mtool.configuration import configuration


class ApiSession:
    def __init__(self):
        pass

    def __enter__(self) -> requests.Session:
        self.session = requests.Session()
        try:
            url = f"{configuration['api_root_url']}/user/automatic-login"
            r = self.session.get(url, params={'token': get_token()})
            r.raise_for_status()
        except requests.exceptions.HTTPError as err:
            logging.exception("Encountered error when logging in using token: \n%s", err)
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()


def get_token() -> str:
    """ Gets a token to log in for the current user """

    # get the session bus
    bus = dbus.SystemBus()
    # get the object
    the_object = bus.get_object("org.nmrbox.notices", "/org/nmrbox/notices")
    # get the interface
    the_interface = dbus.Interface(the_object, "org.nmrbox.notices")

    # NOTE: calling login_token with a uid other than that of the calling process will result in an error
    token = the_interface.login_token(os.getuid())
    return token
