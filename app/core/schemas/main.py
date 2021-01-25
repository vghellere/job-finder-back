from pydantic import BaseModel


class HealthCheck(BaseModel):
    status: int
    message: str

    class Config:
        schema_extra = {
            "example": {
                "status": 200,
                "message": "Everything is working fine here :D"
            }
        }
