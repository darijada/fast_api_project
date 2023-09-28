import arrow
from typing import Dict, Any


def extract_flight_info(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts relevant flight information from the given data dictionary.

    :param data: A dictionary containing flight data.
    :return: A dictionary with extracted flight information.
    """
    flight_info = {}

    flight_info["departure_airport"] = data["itineraries"][0]["segments"][0][
        "departure"
    ]["iataCode"]

    flight_info["arrival_airport"] = data["itineraries"][0]["segments"][-1]["arrival"][
        "iataCode"
    ]

    departure_date_str = data["itineraries"][0]["segments"][0]["departure"]["at"]
    flight_info["departure_date"] = arrow.get(departure_date_str)

    if len(data["itineraries"]) > 1:
        arrival_date_str = data["itineraries"][-1]["segments"][-1]["arrival"]["at"]
        flight_info["arrival_date"] = arrow.get(arrival_date_str)

        flight_info["no_of_stops"] = (
            len(data["itineraries"][0]["segments"])
            + len(data["itineraries"][-1]["segments"])
            - 2
        )
    else:
        flight_info["no_of_stops"] = len(data["itineraries"][0]["segments"]) - 1

    flight_info["no_of_passengers"] = len(data["travelerPricings"])

    flight_info["currency"] = data["price"]["currency"]

    flight_info["price_total"] = float(data["price"]["total"])

    return flight_info
