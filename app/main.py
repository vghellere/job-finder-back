from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from app.core import settings
from app.core.dependencies import get_db
from app.core.schemas.main import HealthCheck
from app.core.routers import candidates


"""
    Using sentry to track application usage and errors, we use the
    FlaskIntegration because it is compatible with FastAPI
"""
sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    integrations=[FlaskIntegration()],
    environment=settings.SENTRY_ENVIRONMENT,
    traces_sample_rate=1.0
)

app = FastAPI()
app.include_router(candidates.router, tags=['candidates'])

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://jobsfinder.viniciusghellere.dev",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
