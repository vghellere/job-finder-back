## About

Job Finder is a simple system where you can search for job candidates.
It is composed of a back-end (this repo) and a [front-end](https://github.com/vghellere/job-finder-front).

It's uses the following technologies:
- FastAPI (Python)
- PyDAL
- MySQL
- ElastciSearch
- Sentry

## Setup

### Environment Variables

You need to define the following environment variables:
- DB_HOST = MySQL hostname:port (Ex.:"localhost:3306")
- DB_NAME = MySQL Database name (Ex.:"jobfinder")
- DB_USER = MySQL Username
- DB_PASSWORD = MySQL Password
- SENTRY_DSN = (Optional) Sentry DSN, can be found in the Sentry Project Settings
- SENTRY_ENVIRONMENT = Sentry Environment (Ex.:"local")
- ELASTIC_HOST = ElasticSearch hostname (Ex.:"localhost")
- ELASTIC_USERNAME = (Optional) ElasticSearch username (Ex.:"localhost")
- ELASTIC_PASSWORD = (Optional) ElasticSearch password (Ex.:"localhost")

### ElasticSearch

You must create an index named "candidates" by using the mappings found in the `app/core/models/candidates_mappings.json` file

### MySQL

The PyDAL automatic database migrations is disabled by default.
To enable it, open the file `app/core/models/database.py` and set `fake_migrate=False` and `fake_migrate_all=False`.

This will make sure that all the needed tables will be created.

## How to run the code

Go the project directory, create a virtual environmnet and activate it.

Run `pip install -r ./app/requirements.txt`

and then run:

`uvicorn app.main:app --reload`
