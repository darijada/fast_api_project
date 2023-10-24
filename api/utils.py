import arrow
from typing import Dict, Any


def extract_flight_info(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts flight information from the given data dictionary.

    :param data: A dictionary containing flight data.
    :return: A dictionary with extracted flight information.
    """
    itineraries = data.get("itineraries", [{}])

    departure_segment = itineraries[0].get("segments", [])
    departure_airport = departure_segment[0].get("departure", {}).get("iataCode", "")
    departure_date_str = departure_segment[0].get("departure", {}).get("at", "")
    departure_date = arrow.get(departure_date_str)
    arrival_airport = departure_segment[-1].get("arrival", {}).get("iataCode", "")

    no_of_stops = 0
    for itinerary in itineraries:
        segments = itinerary.get("segments", [])
        no_of_segments = len(segments) - 1
        no_of_stops += no_of_segments
        for segment in segments:
            no_of_stops += segment.get("numberOfStops", 0)

    traveler_pricings = data.get("travelerPricings", [{}])
    no_of_passengers = len(traveler_pricings)
    currency = data.get("price", {}).get("currency", "")
    price_total = float(data.get("price", {}).get("total", 0))
    departure_geo_distance = data.get("departure_geo_distance", None)
    return_geo_distance = data.get("return_geo_distance", None)

    if len(itineraries) > 1:
        return_segment = itineraries[-1].get("segments", [])
        return_date_str = return_segment[0].get("departure", {}).get("at", "")
        return_date = arrow.get(return_date_str)
    else:
        return_date = None

    flight_info = {
        "departure_airport": departure_airport,
        "arrival_airport": arrival_airport,
        "departure_date": departure_date,
        "return_date": return_date,
        "no_of_stops": str(no_of_stops),
        "no_of_passengers": no_of_passengers,
        "currency": currency,
        "price_total": price_total,
        "departure_geo_distance": departure_geo_distance,
        "return_geo_distance": return_geo_distance,
    }

    return flight_info
