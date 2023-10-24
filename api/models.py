import arrow
import re
from typing import Optional

from pydantic import BaseModel, field_validator, model_validator


class FlightRequestError(Exception):
    """
    Raised when flight request is invalid.
    """


class FlightRequest(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    origin_location_code: str
    destination_location_code: str
    departure_date: str
    return_date: Optional[str]
    adults: int
    children: Optional[int]
    max: int = 250

    @model_validator(mode="before")
    def validate_dates(cls, values):
        departure_date = values.get("departure_date", None)
        return_date = values.get("return_date", None)

        if return_date and return_date < departure_date:
            raise FlightRequestError(
                '"Date From" must be equal or earlier than the "Date To".'
            )
        return values

    @model_validator(mode="before")
    def validate_total_passengers(cls, values):
        adults = values.get("adults", 0)
        children = values.get("children", 0)
        total_passengers = adults + children

        if total_passengers >= 10:
            raise FlightRequestError(
                "The total number of passengers (adults + children) must be less than 10."
            )
        return values

    @field_validator("departure_date", "return_date")
    def convert_arrow_to_utc_string(cls, value: arrow.Arrow) -> str:
        """
        Convert Arrow object to UTC string format.

        :param value: The Arrow object to convert.
        :return: The UTC string representation of the Arrow object.
        """
        return value.format("YYYY-MM-DD")

    def convert_to_dict(self) -> dict:
        """
        Convert the instance values to a dictionary with camel case keys.

        :return: A dictionary with camel case keys.
        """
        data = self.model_dump()
        converted_data = {}
        for key, value in data.items():
            if value:
                converted_key = re.sub(r"_([a-z])", lambda m: m.group(1).upper(), key)
                converted_data[converted_key] = value
        return converted_data


class FlightOffer(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    departure_airport: str
    arrival_airport: str
    departure_date: arrow.Arrow
    return_date: Optional[arrow.Arrow]
    no_of_stops: str
    no_of_passengers: int
    currency: str
    price_total: float
    departure_geo_distance: Optional[float]
    return_geo_distance: Optional[float]

    @field_validator("departure_date", "return_date")
    def convert_formatted_utc_to_arrow(cls, value: str) -> Optional[arrow.Arrow]:
        """
        Convert formatted UTC time string to an Arrow object.

        :param value: The formatted UTC time string.
        :return: The Arrow object representing the time or None if parsing fails.
        """
        try:
            return arrow.get(value)
        except (arrow.ParserError, TypeError):
            return None
