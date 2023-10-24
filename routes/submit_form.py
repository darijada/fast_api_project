import json
import arrow
from datetime import datetime

from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from api.amadeus_api import get_flight_offers, get_airport_geolocation
from api.models import FlightRequest, FlightOffer, FlightRequestError
from caching.cache import (
    get_cache_db,
    CachedFlightOffer,
    ArrowJSONEncoder,
    CENTRAL_EUROPE_TIME,
)
from templates.utils import format_currency


router = APIRouter()
templates = Jinja2Templates(directory="templates")
templates.env.filters["format_currency"] = format_currency


@router.post("/submit-form")
async def submit_form(request: Request, cache_db: Session = Depends(get_cache_db)):
    """
    Handles the submission of a flight search form. It retrieves flight offers based on the
    form data and caches them for future use. If cached flight offers are available for the
    same search criteria, it returns cached data; otherwise, it queries flight offers from
    the Amadeus API.

    :param request: The FastAPI request object
    :param cache_db: The SQLAlchemy database session used for caching flight offers
    :return: A TemplateResponse containing the rendered flight offers template with search results
    """
    form_data = await request.form()

    departure = str(form_data.get("departure"))
    arrival = str(form_data.get("arrival"))
    date_from = str(form_data.get("date_from"))
    date_to = str(form_data.get("date_to"))
    adult_passengers = int(str(form_data.get("adult_passengers")))
    children = (
        int(str(form_data.get("children")))
        if str(form_data.get("children")) != "None"
        else 0
    )

    invalid_no_of_passengers = False
    invalid_dates = False

    flight_offers = []

    if departure and arrival:
        cached_offers = (
            cache_db.query(CachedFlightOffer)
            .filter(
                CachedFlightOffer.departure == departure,
                CachedFlightOffer.arrival == arrival,
                CachedFlightOffer.date_from == datetime.strptime(date_from, "%Y-%m-%d"),
                CachedFlightOffer.date_to
                == (datetime.strptime(date_to, "%Y-%m-%d") if date_to else None),
                CachedFlightOffer.adults == adult_passengers,
                CachedFlightOffer.children == children,
            )
            .first()
        )

        if cached_offers:
            flight_offers_data = json.loads(cached_offers.flight_offers)

            for offer_data in flight_offers_data:
                offer_data["departure_date"] = arrow.get(offer_data["departure_date"])
                offer_data["return_date"] = (
                    arrow.get(offer_data["return_date"])
                    if offer_data["return_date"]
                    else None
                )
                flight_offers.append(FlightOffer(**offer_data))
        else:
            try:
                flight_request = FlightRequest(
                    origin_location_code=departure,
                    destination_location_code=arrival,
                    departure_date=date_from,
                    return_date=date_to,
                    adults=adult_passengers,
                    children=children,
                )

                flight_offers = await get_flight_offers(flight_request)

                cache_entry = CachedFlightOffer(
                    departure=departure,
                    arrival=arrival,
                    date_from=datetime.strptime(date_from, "%Y-%m-%d"),
                    date_to=datetime.strptime(date_to, "%Y-%m-%d") if date_to else None,
                    adults=adult_passengers,
                    children=children,
                    flight_offers=json.dumps(
                        [offer.model_dump() for offer in flight_offers],
                        cls=ArrowJSONEncoder,
                    ),
                )
                cache_db.add(cache_entry)
                cache_db.commit()

            except FlightRequestError:
                if adult_passengers + children > 9:
                    invalid_no_of_passengers = True
                if date_from > date_to:
                    invalid_dates = True

    return templates.TemplateResponse(
        "flight_offers.html",
        {
            "request": request,
            "today_date": CENTRAL_EUROPE_TIME.date(),
            "flight_offers": flight_offers,
            "departure": departure,
            "arrival": arrival,
            "date_from": datetime.strptime(date_from, "%Y-%m-%d"),
            "date_to": datetime.strptime(date_to, "%Y-%m-%d") if date_to else None,
            "invalid_no_of_passengers": invalid_no_of_passengers,
            "invalid_dates": invalid_dates,
        },
    )
