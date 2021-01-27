from pydantic import BaseModel
from typing import List, Optional
from .city import City
from .technology import Technology


class CandidateImportResult(BaseModel):
    candidates_imported: int

    class Config:
        schema_extra = {
            "example": {
                "candidates_imported": 100
            }
        }


class Candidate(BaseModel):
    id: int
    city: City
    experience_min: int
    experience_max: int
    technologies: List[Technology]


class CandidateSearchResult(BaseModel):
    candidates: List[Candidate]


class CandidateSearchOptions(BaseModel):
    cities: List[City]
    technologies: List[Technology]
    experience_min: int
    experience_max: int
