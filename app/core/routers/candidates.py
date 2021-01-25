import requests
import re
from fastapi import APIRouter, Response, Depends
from app.core.schemas.candidates import CandidateImportResult
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
