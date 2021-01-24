from .models.database import retrieve_dal_connection
from . import settings


def get_db():
    """Get a new or existing database connection and yields it, after which
    the connection is closed and returned to the connection pool

    Yields:
        DAL: pyDAL connection object
    """
    db = retrieve_dal_connection(
        db_host=settings.DB_HOST,
        db_name=settings.DB_NAME,
        db_user=settings.DB_USER,
        db_password=settings.DB_PASSWORD,
    )

    try:
        yield db
    finally:
        db.close()
