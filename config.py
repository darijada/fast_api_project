from decouple import config

from pydantic_settings import BaseSettings


class CfgSettings(BaseSettings):
    """
    A class which loads settings from a .env file.
    """

    AUTHORIZATION_URL: str = config("URL")
    AUTHORIZATION_GRANT_TYPE: str = config("GRANT_TYPE")
    AUTHORIZATION_CLIENT_ID: str = config("CLIENT_ID")
    AUTHORIZATION_CLIENT_SECRET: str = config("CLIENT_SECRET")

    API_AIRPORT_URL: str = config("AIRPORT_URL")
    API_FLIGHT_OFFERS_URL: str = config("FLIGHT_OFFERS_URL")

    DATABASE_URL: str = config("DATABASE_URL")


settings = CfgSettings()
