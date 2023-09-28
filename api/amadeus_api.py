from typing import List, Dict, Any, Optional
import httpx
import difflib

from config import settings

from api.models import FlightRequest, FlightOffer
from api.utils import extract_flight_info


class AmadeusAPIError(Exception):
    """
    Raised when an exception occurs while requesting or parsing data from Amadeus API.
    """


def get_access_token() -> Any:
    """
    Retrieves an access token from the Amadeus API using the configuration settings.

    :return: The access token as a string.
    :raises AmadeusAPIError: If there is an error making a request to the Amadeus API.
    """
    try:
        response = httpx.post(
            url=settings.AUTHORIZATION_URL,
            data={
                "grant_type": settings.AUTHORIZATION_GRANT_TYPE,
                "client_id": settings.AUTHORIZATION_CLIENT_ID,  # Replace with your actual client_id
                "client_secret": settings.AUTHORIZATION_CLIENT_SECRET,
            },
        )
        return response.json()["access_token"]

    except httpx.HTTPError:
        msg = f"Error making a request to the Amadeus API."
        raise AmadeusAPIError(msg)


async def get_flight_offers(request_body: FlightRequest) -> List[FlightOffer]:
    """
    Retrieves flight offers from the Amadeus API based on the given request body.

    :param request_body: The FlightRequest object containing the flight search criteria.
    :return: A list of FlightOffer objects representing the flight offers.
    :raises AmadeusAPIError: If there is an error making a request to the Amadeus API.
    """
    access_token = get_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        response = httpx.get(
            url=settings.API_FLIGHT_OFFERS_URL,
            headers=headers,
            params=request_body.convert_to_dict(),
            timeout=15,
        )

        json_response = response.json()["data"]

        flight_offers = [
            FlightOffer(**extract_flight_info(offer)) for offer in json_response
        ]

        sorted_flight_offers = sorted(
            flight_offers, key=lambda offer: offer.price_total
        )

        return sorted_flight_offers

    except httpx.HTTPError:
        msg = f"Error making a request to the Amadeus API."
        raise AmadeusAPIError(msg)


async def get_location_iata_code(location: str) -> Optional[str]:
    """
    Retrieves the IATA code for a given location name from the Amadeus API.

    :param location: The name of the location for which to retrieve the IATA code.
    :return: The IATA code of the location, or None if the code is not found.
    :raises AmadeusAPIError: If there is an error making a request to the Amadeus API.
    """
    access_token = get_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"keyword": location}

    try:
        response = httpx.get(
            url=settings.API_LOCATION_URL,
            headers=headers,
            params=params,
            timeout=15,
        )

        json_response = response.json()

        if not json_response or "warnings" in json_response:
            return None

        response_data = [
            flight for flight in json_response["data"] if "iataCode" in flight
        ]
        if len(response_data) > 1:
            matching_loc = closest_matching_location(location, response_data)

            if matching_loc:
                return matching_loc.get("iataCode", "")
            else:
                return None
        else:
            return response_data[0].get("iataCode", "") if response_data else None

    except httpx.HTTPError:
        msg = f"Error making a request to the Amadeus API."
        raise AmadeusAPIError(msg)


def closest_matching_location(
    location_name: str, location_data: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """
    Finds the closest matching location from a list of locations based on the provided name.

    :param location_name: The name of the location to find a match for.
    :param location_data: A list of location data dictionaries.
    :return: The closest matching location data dictionary, or None if no match is found.
    """
    locations = [loc["name"] for loc in location_data]
    matches = difflib.get_close_matches(location_name, locations)

    if matches:
        closest_match = matches[0]
        for loc in location_data:
            if loc["name"] == closest_match:
                closest_match = loc
        return closest_match
    else:
        return None
