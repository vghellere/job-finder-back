import requests
import re
from fastapi import APIRouter, Response, Depends
from typing import Optional, List
from app.core.schemas.candidates import CandidateImportResult, \
                                        CandidateSearchResult, \
                                        Technologie, City, Candidate
from app.core.dependencies import get_db

router = APIRouter(
    prefix="/candidates"
)


def _read_candidates_from_s3():
    """Reads the candidate JSON file from S3

    Returns:
        list[dict]: List of candidates
    """
    file_url = "https://geekhunter-recruiting.s3.amazonaws.com/code_challenge.json"
    file_request = requests.get(file_url, timeout=5)

    response_json = file_request.json()
    return response_json['candidates']


def _import_cities(db, candidates):
    """Import Cities into the DB

    Args:
        db (DAL): pyDAL connection object
        candidates (list[dict]): List of candidates
    """
    cities = set(map(lambda candidate: candidate['city'], candidates))
    for city in cities:
        db.city.update_or_insert(
            db.city.name == city,
            name=city
        )


def _import_technologies(db, candidates):
    """Import Technologies into the DB

    Args:
        db (DAL): pyDAL connection object
        candidates (list[dict]): List of candidates
    """
    tech_set = set()
    for candidate in candidates:
        for tech in candidate['technologies']:
            tech_set.add(tech['name'])

    for tech in tech_set:
        db.tech.update_or_insert(
            db.tech.name == tech,
            name=tech
        )


def _extract_years_min_max_from_experience(experience):
    """Extract years of experience from string

    Args:
        experience (str): Years of experience. Ex.: '0-1 years' or '12+ years'

    Returns:
        int, int: Minimum and maximum years of experience
    """
    # '0-1 years'
    match_groups = re.findall(r'(\d+)-(\d+).*', experience)
    if len(match_groups) > 0:
        min = int(match_groups[0][0])
        max = int(match_groups[0][1])
        return min, max

    # '12+ years'
    match_groups = re.findall(r'(\d+)\+.*', experience)
    if len(match_groups) > 0:
        min = int(match_groups[0])
        max = 99
        return min, max


def _import_candidates_to_db(db, candidates):
    """Import candidates into the DB

    Args:
        db (DAL): pyDAL connection object
        candidates (list[dict]): List of candidates

    Returns:
        int: Number of candidates imported
    """
    candidates_import = 0
    for candidate in candidates:
        city = db(db.city.name == candidate['city']).select().first()
        years_min, years_max = _extract_years_min_max_from_experience(candidate['experience'])

        db.candidate.update_or_insert(
            db.candidate.id == candidate['id'],
            id=candidate['id'],
            city_id=city.id,
            years_experience_min=years_min,
            years_experience_max=years_max,
        )

        for tech in candidate['technologies']:
            tech_id = db(db.tech.name == tech['name']).select().first().id

            db.candidate_tech_reference.update_or_insert(
                (db.candidate_tech_reference.candidate_id == candidate['id'])
                & (db.candidate_tech_reference.tech_id == tech_id),
                candidate_id=candidate['id'],
                tech_id=tech_id,
                is_main_tech=tech['is_main_tech']
            )

        candidates_import += 1

    return candidates_import


def _import_candidates(db):
    """Read candidate list from S3 and import them into the DB

    Args:
        db (DAL): pyDAL connection object

    Returns:
        int: Number of candidates imported
    """
    candidates = _read_candidates_from_s3()

    _import_cities(db, candidates)
    _import_technologies(db, candidates)
    candidates_imported = _import_candidates_to_db(db, candidates)

    db.commit()
    return candidates_imported


@router.post(
    "/import",
    name="Candidates Import",
    description="""Import candidates from S3 JSON file into the Database""",
    response_model=CandidateImportResult,
    responses={
        200: {
            "candidates_imported": 100
        }
    }
)
async def import_candidates(response: Response, db=Depends(get_db)):
    candidates_imported = _import_candidates(db)
    response.status_code = 201
    return CandidateImportResult(candidates_imported=candidates_imported)


def _get_candidate_techs(db, candidate_id):
    """Returns a list of the candidate technologies based on candidate_id

    Args:
        db (DAL): pyDAL connection object
        candidate_id (int): Candidate ID

    Returns:
        list[Technologie]: List of the candidates techs
    """
    technologies = []
    techs = db(
        (db.candidate_tech_reference.tech_id == db.tech.id)
        & (db.candidate_tech_reference.candidate_id == candidate_id)
    ).select()

    for tech in techs:
        technologie = Technologie(
            id=tech.tech.id,
            name=tech.tech.name,
            is_main_tech=tech.candidate_tech_reference.is_main_tech
        )
        technologies.append(technologie)
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
        CandidateSearchResult: List of matched candidates
    """
    matches_result = CandidateSearchResult(candidates=[])

    tech_count = db.tech.id.count()
    years_min = db.candidate.years_experience_min.max()
    years_max = db.candidate.years_experience_max.max()

    matches_query = db(
        (db.candidate.city_id == db.city.id)
        & (db.candidate_tech_reference.candidate_id == db.candidate.id)
        & (db.candidate_tech_reference.tech_id == db.tech.id)
        & (db.candidate.years_experience_min >= experience_min)
        & (db.candidate.years_experience_max <= experience_max)
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

        matches_result.candidates.append(candidate)
    return matches_result


@router.get(
    "",
    name="Search for candidates",
    description="""Search for candidates based on filters

The algorithm selects the top 5 matches based first on years of experience
then in the number of technologies the candidate knows

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
    matches_result = _search_candidates(
        db, city_id, experience_min, experience_max, techs
    )

    return matches_result
