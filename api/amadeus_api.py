import time
import httpx
from typing import List, Any, Tuple, Optional, Dict
from geopy import distance

from config import settings

from api.models import FlightRequest, FlightOffer
from api.utils import extract_flight_info


AMADEUS_REQUEST_TIMEOUT = 60
DELAY_BETWEEN_API_CALLS = 0.8


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
                "client_id": settings.AUTHORIZATION_CLIENT_ID,
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
            timeout=AMADEUS_REQUEST_TIMEOUT,
        )

        flight_offers_json_response = response.json()["data"]

        airports_geo_coordinates = get_offer_airports_geolocations(response.json())

        flight_offers_json_response = calculate_and_set_geo_distances(
            flight_offers_json_response, airports_geo_coordinates
        )

        flight_offers = [
            FlightOffer(**extract_flight_info(offer))
            for offer in flight_offers_json_response
        ]

        sorted_flight_offers = sorted(
            flight_offers, key=lambda offer: offer.price_total
        )

        return sorted_flight_offers

    except:
        msg = f"Error making a request to the Amadeus API."
        raise AmadeusAPIError(msg)


def get_airport_geolocation(iata_code: str) -> Optional[Tuple]:
    """
    Retrieves the geographical coordinates (latitude and longitude) of an airport based on its IATA code.

    :param iata_code: The IATA code of the airport.
    :return: A tuple containing latitude and longitude or None if not found.
    :raises AmadeusAPIError: If there is an error making a request to the Amadeus API.
    """
    access_token = get_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        response = httpx.get(
            url=settings.API_AIRPORT_URL,
            headers=headers,
            params={"keyword": iata_code, "subType": "AIRPORT"},
            timeout=AMADEUS_REQUEST_TIMEOUT,
        )

        json_response = response.json()["data"]

        if json_response:
            for airport in json_response:
                if airport["iataCode"] == iata_code:
                    airport_geo_location = airport["geoCode"]
                    return (
                        airport_geo_location["latitude"],
                        airport_geo_location["longitude"],
                    )
        else:
            return None

    except:
        msg = f"Error making a request to the Amadeus API."
        raise AmadeusAPIError(msg)


def get_offer_airports_geolocations(
    flight_offers_data: Dict[str, Any]
) -> Dict[str, Optional[Tuple]]:
    """
    Retrieves the geographical coordinates of airports referenced in flight offers data.

    :param flight_offers_data: Flight offers data received from the Amadeus API.
    :return: A dictionary mapping airport IATA codes to their geographical coordinates.
    :raises AmadeusAPIError: If there is an error making a request to the Amadeus API.
    """
    airports_geo_coordinates = {}
    airports = flight_offers_data.get("dictionaries", {}).get("locations", {})
    airport_iata_codes = [code for code in airports]
    offers = flight_offers_data.get("data", [])

    if offers:
        for offer in offers:
            airport_iata_codes.extend(get_airport_iata_codes_from_offer(offer))

    for airport in airport_iata_codes:
        airports_geo_coordinates[airport] = get_airport_geolocation(airport)
        time.sleep(DELAY_BETWEEN_API_CALLS)  # Pause between API calls

    return airports_geo_coordinates


def get_airport_iata_codes_from_offer(offer: Dict[str, Any]) -> List[str]:
    """
    Extracts airport IATA codes from a flight offer.

    :param offer: A flight offer data dictionary.
    :return: A list of airport IATA codes referenced in the flight offer.
    """
    iata_codes = []
    itineraries = offer.get("itineraries", [])
    for itinerary in itineraries:
        segments = itinerary.get("segments", [])
        for segment in segments:
            stops = segment.get("stops", [])
            for stop in stops:
                iata_codes.append(stop["iataCode"])
    return iata_codes


def calculate_and_set_geo_distances(
    flight_offers: Dict[str, Any], airports_geo_coordinates: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Calculates and sets the geographical distances for flight offers based on airport coordinates.

    :param flight_offers: Flight offers data.
    :param airports_geo_coordinates: Dictionary mapping airport IATA codes to their geographical coordinates.
    :return: Modified flight offers data with added distance information.
    """
    for offer in flight_offers:
        departure = offer.get("itineraries", [])[0]
        departure_segments = departure.get("segments")
        departure_airport_iata_codes = []

        for flight in departure_segments:
            if flight["departure"]["iataCode"] not in departure_airport_iata_codes:
                departure_airport_iata_codes.append(flight["departure"]["iataCode"])

            if "stops" in flight:
                for flight_stop in flight.get("stops"):
                    if flight_stop["iataCode"] not in departure_airport_iata_codes:
                        departure_airport_iata_codes.append(flight_stop["iataCode"])

            if flight["arrival"]["iataCode"] not in departure_airport_iata_codes:
                departure_airport_iata_codes.append(flight["arrival"]["iataCode"])

            departure_distance = calculate_distance(
                departure_airport_iata_codes, airports_geo_coordinates
            )
            offer["departure_geo_distance"] = (
                round(departure_distance, 2) if departure_distance else None
            )

        if len(offer.get("itineraries", [])) > 1:
            return_flight = offer.get("itineraries", [])[1]
            return_segments = return_flight.get("segments")
            return_airport_iata_codes = []

            for flight in return_segments:
                if flight["departure"]["iataCode"] not in return_airport_iata_codes:
                    return_airport_iata_codes.append(flight["departure"]["iataCode"])

                if "stops" in flight:
                    for flight_stop in flight.get("stops"):
                        if flight_stop["iataCode"] not in return_airport_iata_codes:
                            return_airport_iata_codes.append(flight_stop["iataCode"])

                if flight["arrival"]["iataCode"] not in return_airport_iata_codes:
                    return_airport_iata_codes.append(flight["arrival"]["iataCode"])
            return_distance = calculate_distance(
                return_airport_iata_codes, airports_geo_coordinates
            )
            offer["return_geo_distance"] = (
                round(return_distance, 2) if return_distance else None
            )

    return flight_offers


def calculate_distance(airport_iata_codes, airports_geo_coordinates) -> float:
    """
    Calculates the total geographical distance between a series of airports based on their IATA codes.

    :param airport_iata_codes: A list of airport IATA codes in the order of the flight route.
    :param airports_geo_coordinates: Dictionary mapping airport IATA codes to their geographical coordinates.
    :return: The total geographical distance in kilometers.
    """
    distance_total = 0.0

    for i in range(len(airport_iata_codes) - 1):
        airport_code_one, airport_code_two = (
            airport_iata_codes[i],
            airport_iata_codes[i + 1],
        )
        geo_coordinate_one, geo_coordinate_two = airports_geo_coordinates.get(
            airport_code_one
        ), airports_geo_coordinates.get(airport_code_two)

        if geo_coordinate_one and geo_coordinate_two:
            distance_total += distance.distance(
                geo_coordinate_one, geo_coordinate_two
            ).kilometers

    return distance_total
