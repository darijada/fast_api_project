import os
from typing import Dict

from configparser import ConfigParser
from pydantic import BaseSettings, HttpUrl, validator

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CFG_FILE_PATH = os.path.join(BASE_DIR, "settings.cfg")


class CfgSettings(BaseSettings):
    """
    A class which loads settings from a .cfg file.
    """
    AUTHORIZATION_URL: str
    AUTHORIZATION_GRANT_TYPE: str
    AUTHORIZATION_CLIENT_ID: str
    AUTHORIZATION_CLIENT_SECRET: str

    API_FLIGHT_OFFERS_URL: str
    API_LOCATION_URL: str

    DATABASE_URL: str


def load_cfg_settings() -> CfgSettings:
    """
    Read configuration settings in ConfigParser format and populate a CfgSettings instance with the values.

    :return: An instance of the populated CfgSettings class.
    :raises FileNotFoundError: If the configuration file (CFG_FILE_PATH) cannot be loaded.
    """
    parser = ConfigParser()
    loaded = parser.read(CFG_FILE_PATH)

    if not loaded:
        raise FileNotFoundError(f"Could not load {CFG_FILE_PATH}")

    else:
        settings_as_dict: Dict[str, str] = dict()
        for section in parser.sections():
            section_key = section.upper()
            for k, v in parser[section].items():
                full_key = f"{section_key}_{k.upper()}"
                settings_as_dict[full_key] = v

    return CfgSettings(**settings_as_dict)


settings = load_cfg_settings()
