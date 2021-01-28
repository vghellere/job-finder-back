from fastapi import APIRouter, Response, Depends, HTTPException, Request
from typing import Optional
from requests.auth import HTTPBasicAuth
import requests
from sentry_sdk import capture_exception, push_scope
from ..schemas.candidates import CandidateSearchResult, Candidate, \
                                        CandidateSearchOptions
from ..schemas.city import City
from ..schemas.technology import Technology
from ..dependencies import get_db
from ..models.elasticsearch import get_elastic_base_url, \
                                          get_elastic_credentials
from .. import settings


router = APIRouter(
    prefix="/candidates"
)


def _get_candidate_techs(db, candidate_id):
    """Returns a list of the candidate technologies based on candidate_id

    Args:
        db (DAL): pyDAL connection object
        candidate_id (int): Candidate ID

    Returns:
        list[Technology]: List of the candidates techs
    """
    technologies = []
    techs = db(
        (db.candidate_tech_reference.tech_id == db.tech.id)
        & (db.candidate_tech_reference.candidate_id == candidate_id)
    ).select()

    for tech in techs:
        technology = Technology(
            id=tech.tech.id,
            name=tech.tech.name,
            is_main_tech=tech.candidate_tech_reference.is_main_tech
        )
        technologies.append(technology)
    return technologies


def _search_candidates(db, city_id, experience_min, experience_max, techs):
    """Match candidates with the specified parameters and returns them

    Args:
        db (DAL): pyDAL connection object
        city_id (int): City ID
        experience_min (int): Minimum Years of experience
        experience_max (int): Maximum Years of experience
        techs (str): Comma separated string of Tech IDs

    Returns:
        list(Candidate): List of matched candidates
    """
    candidates = []

    tech_count = db.tech.id.count()
    years_min = db.candidate.years_experience_min.max()
    years_max = db.candidate.years_experience_max.max()

    matches_query = db(
        (db.candidate.city_id == db.city.id)
        & (db.candidate_tech_reference.candidate_id == db.candidate.id)
        & (db.candidate_tech_reference.tech_id == db.tech.id)
        & (db.candidate.years_experience_min >= experience_min)
        & (
            (db.candidate.years_experience_max <= experience_max)
            | ((db.candidate.years_experience_max == 99)
                & (db.candidate.years_experience_min <= experience_max))
        )
    )

    if city_id:
        matches_query = matches_query(
            db.candidate.city_id == city_id
        )

    if techs:
        techs_list = techs.split(',')
        matches_query = matches_query(
            db.candidate_tech_reference.tech_id.belongs(techs_list)
        )

    matches = matches_query.select(
        db.candidate.ALL,
        db.city.ALL,
        tech_count,
        years_min,
        years_max,
        groupby=db.candidate.id,
        orderby=[~years_max, ~tech_count],
        limitby=(0, 5)
    )

    for match in matches:
        city = City(id=match.city.id, name=match.city.name)
        technologies = _get_candidate_techs(db, match.candidate.id)
        candidate = Candidate(
            id=match.candidate.id,
            city=city,
            experience_min=match.candidate.years_experience_min,
            experience_max=match.candidate.years_experience_max,
            technologies=technologies
        )

        candidates.append(candidate)
    return candidates


@router.get(
    "",
    name="Search for candidates",
    description="""Search for candidates based on filters

The algorithm selects the top 5 matches based first on years of experience
then in the number of technologies the candidate knows.

If there aren't 5 primary results a secondary search will be performed
increasing the 'experience_max' parameter to 99

    TODO: Improve technologies matching
    """,
    response_model=CandidateSearchResult,
    responses={
        200: {
        }
    }
)
async def search_candidates(city_id: Optional[int] = None,
                            experience_min: Optional[int] = 0,
                            experience_max: Optional[int] = 99,
                            techs: Optional[str] = None,
                            db=Depends(get_db)):
    matches_result = CandidateSearchResult(
        main_candidates=[],
        secondary_candidates=[]
    )

    main_results = _search_candidates(
        db, city_id, experience_min, experience_max, techs
    )

    if len(main_results) < 5:
        experience_max = 99
        extra_results = _search_candidates(
            db, city_id, experience_min, experience_max, techs
        )

        main_results_ids = list(
            map(lambda candidate: candidate.id, main_results)
        )

        secondary_results = []
        for extra_result in extra_results:
            if not(extra_result.id in main_results_ids):
                secondary_results.append(extra_result)

        matches_result.secondary_candidates = secondary_results

    matches_result.main_candidates = main_results

    return matches_result


def _get_city_options(db):
    """Gets all available cities from the database

    Args:
        db (DAL): pyDAL connection object

    Returns:
        list[City]: List of City
    """
    cities = []
    cities_query = db(db.city.id > 0).select(orderby=db.city.name)

    for city in cities_query:
        cities.append(
            City(id=city.id, name=city.name)
        )

    return cities


def _get_tech_options(db):
    """Gets all available technologies from the database

    Args:
        db (DAL): pyDAL connection object

    Returns:
        list[Technology]: List of Technology
    """
    techs = []
    techs_query = db(db.tech.id > 0).select(orderby=db.tech.name)

    for tech in techs_query:
        techs.append(
            Technology(id=tech.id, name=tech.name)
        )

    return techs


def _get_search_options(db):
    """Create the CandidateSearchOptions object containing all cities and
    technologies from the database

    Args:
        db (DAL): pyDAL connection object

    Returns:
        CandidateSearchOptions: Object with available search options
    """
    city_options = _get_city_options(db)
    tech_options = _get_tech_options(db)
    search_options = CandidateSearchOptions(
        cities=city_options,
        technologies=tech_options,
        experience_min=0,
        experience_max=99
    )

    return search_options


@router.get(
    "/search-options",
    name="Returns search options to be used in the /candidates endpoint",
    description="""Returns search options to be used in the /candidates
endpoint

    TODO: Cache the response of this endpoint
    """,
    response_model=CandidateSearchOptions,
    responses={
        200: {
        }
    }
)
async def search_options(db=Depends(get_db)):
    search_options = _get_search_options(db)

    return search_options


@router.post(
    "/elastic-proxy/candidates/_msearch",
    name='Proxy for searching candidates in Elastic',
    description="""This endpoint receives a request from ReactiveSearch,
    forward the request to ElasticSearch and returns the results.
    Additional check could be performed here
    like user authorization or customized filters""")
async def elastic_proxy_candidates(request: Request):
    """This endpoint is used as a proxy for making searches in ElasticSearch
    'candidates' index. It is called by the ReactiveSearch Front-End component.
    
    What this code does:
    - Makes search request to ElasticSearch
    - Returns Elastic response to the front-end

    Args:
        request (Request): FastAPI Request Object from which we get the POST
        Body

    Raises:
        HTTPException: raises exception 400

    Returns:
        (dict): Elasticsearch response
    """
    body = await request.body()

    es_url = '{}candidates/_msearch?'.format(get_elastic_base_url())
    es_user, es_password = get_elastic_credentials()
    headers = {'Content-Type': 'application/x-ndjson'}

    es_request = requests.post(
        es_url,
        auth=HTTPBasicAuth(es_user, es_password),
        headers=headers,
        data=body,
        timeout=10
    )
    
    if es_request.status_code != 200:
        error_message = "Error performing the search"
        with push_scope() as scope:
            scope.set_context(
                "data",
                {
                    "elasticRequest": body,
                    "elasticReponse": es_request.text
                }
            )
            capture_exception(Exception(error_message))
        raise HTTPException(status_code=es_request.status_code,
                            detail=error_message)

    request_response = es_request.json()
    return request_response
