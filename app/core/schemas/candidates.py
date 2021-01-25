from pydantic import BaseModel


class CandidateImportResult(BaseModel):
    candidates_imported: int

    class Config:
        schema_extra = {
            "example": {
                "candidates_imported": 100
            }
        }
