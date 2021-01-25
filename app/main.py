from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse, Response
from app.core.dependencies import get_db
from app.core.schemas.main import HealthCheck

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Access /docs for API documentation"}


@app.get(
    "/health-check",
    name="Health Check",
    description="""Health check endpoint to be used by monitoring softwares
    such as UptimeCheck or Kubernetes Health Check""",
    response_model=HealthCheck,
    responses={
        200: {
            "description": "Health check passed, everything is fine.",
        },
        503: {
            "description": "Service unavailable.",
        }
    }
)
async def health_check(response: Response, db=Depends(get_db)):
    response_model = HealthCheck(
        status=200,
        message="Everything is working fine here :D"
    )

    try:
        db.executesql("select 1;")
    except:
        response_model.status = 503
        response_model.message = "Database unavailable"

    response.status_code = response_model.status
    return response_model
