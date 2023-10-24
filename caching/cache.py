import json
import arrow
import atexit
import pytz
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler

from sqlalchemy import (
    create_engine,
    inspect,
    Column,
    Integer,
    String,
    DateTime,
    text,
)
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


CENTRAL_EUROPE_TIMEZONE = pytz.timezone("Europe/Berlin")
CENTRAL_EUROPE_TIME = datetime.now(CENTRAL_EUROPE_TIMEZONE)

DATABASE_URL = "postgresql://postgres:postgres@localhost/amadeus_flights"
ENGINE = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=ENGINE)
CLEAR_CACHE_INTERVAL = 30

Base = declarative_base()

scheduler = BackgroundScheduler()


class CachedFlightOffer(Base):
    __tablename__ = "cached_flight_offers"

    id = Column(Integer, primary_key=True, index=True)
    departure = Column(String)
    arrival = Column(String)
    date_from = Column(DateTime)
    date_to = Column(DateTime)
    adults = Column(Integer)
    children = Column(Integer)
    flight_offers = Column(String)
    created_at = Column(DateTime, server_default=text("now()"))


# Create caching table if it isn't created
inspector = inspect(ENGINE)
if not inspector.has_table("cached_flight_offers"):
    Base.metadata.create_all(bind=ENGINE)


class ArrowJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, arrow.Arrow):
            return obj.format("YYYY-MM-DDTHH:mm:ss")
        return super(ArrowJSONEncoder, self).default(obj)


def get_cache_db():
    """
    Get a SQLAlchemy database session for caching flight offers.

    :return: A SQLAlchemy database session.
    """
    db = SessionLocal()
    return db


def clear_cache_db():
    """
    Clear outdated cached flight offers from the database that are older than
    30 minutes ago from the Central Europe time.
    """
    db = get_cache_db()
    one_hour_ago = CENTRAL_EUROPE_TIME - timedelta(minutes=30)
    db.query(CachedFlightOffer).filter(
        CachedFlightOffer.created_at < one_hour_ago
    ).delete()
    db.commit()


# Schedule the task to run every 30 minutes
scheduler.add_job(clear_cache_db, trigger="interval", minutes=30)

# Start the scheduler
scheduler.start()

# Shut down the scheduler
atexit.register(lambda: scheduler.shutdown())
