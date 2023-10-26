# Low-cost Flights

A web application for searching low-cost flights retrieved from Amadeus API.

## Prerequisites

* [Python 3](https://www.python.org/downloads/)
* [pip](https://pip.pypa.io/en/stable/installation/)
* [PostgreSQL](https://www.postgresql.org/download/)


## Configuration

The `.env` file is used to store sensitive configuration data. To create and configure a `.env` file, follow next steps:
* Create a `.env` file in project's root directory
* Add next environment variables that are needed:

        URL=https://test.api.amadeus.com/v1/security/oauth2/token
        GRANT_TYPE=client_credentials
        CLIENT_ID=my_amadeus_api_key
        CLIENT_SECRET=my_amadeus_api_secret
        FLIGHT_OFFERS_URL=https://test.api.amadeus.com/v2/shopping/flight-offers
        AIRPORT_URL=https://test.api.amadeus.com/v1/reference-data/locations      
        DATABASE_URL=postgresql://username:password@localhost:5432/amadeus_flights


## Setup

To get the web application up and running locally, following steps are required:
  * Clone the repository
  * Create a virtual environment (in project's root directory):
    
          Linux/macOS:   python3 -m venv .fastapi_env
          Windows:       py -m venv .fastapi_env

  * Activate virtual environment

          Linux/macOS:   source .fastapi_env/bin/activate
          Windows:       .\.fastapi_env\Scripts\activate

  * Install dependencies using `pip install -r requirements.txt`
  * Run the app using `uvicorn main:app --reload`
  * Access the web application at `http://localhost:8000`


## Usage

Low-cost flight web application retrieves flight offer as a response to sent request to the Amadeus API with parameters
such as departure and arrival airport IATA codes, travel dates and the number of passengers. 

To enhance performance and ensure efficiency, flight offers retrieved from the Amadeus API are cached within a 
PostgreSQL database for future usage. Cached flight data remains accessible for a limited duration, with a predefined 
lifespan of 30 minutes. 

PostgreSQL database `amadeus_flights` is automatically created during the initial execution of the application.

Important thing to mention is that if you are using the Amadeus test environment, only a subset of their data is 
available. If you want to have access to the full content you will need to move to production. 

You can find provided collection of accessible data for the Amadeus test environment at: 
[amadeus4dev/data-collection](https://github.com/amadeus4dev/data-collection).
