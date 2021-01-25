from pydantic import BaseModel
from typing import List


class CandidateImportResult(BaseModel):
    candidates_imported: int

    class Config:
        schema_extra = {
            "example": {
                "candidates_imported": 100
            }
        }


class City(BaseModel):
    id: int
    name: str


class Technologie(BaseModel):
    id: int
    name: str
    is_main_tech: bool


class Candidate(BaseModel):
    id: int
    city: City
    experience_min: int
    experience_max: int
    technologies: List[Technologie]


class CandidateSearchResult(BaseModel):
    candidates: List[Candidate]
