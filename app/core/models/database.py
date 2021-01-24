from pydal import DAL


def retrieve_dal_connection(db_host, db_name, db_user, db_password):
    """Create pyDAL connection or retrieves it from the connection pool

    Args:
        db_host (str): Database hostname and port, ex.: "localhost:3306"
        db_name (str): Database schema name
        db_user (str): Databse user
        db_password (str): Database password

    Returns:
        DAL: pyDAL connection object
    """
    uri = "mysql://{0}:{1}@{2}/{3}".format(db_user, db_password, db_host,
                                           db_name)
    db = DAL(
        uri,
        pool_size=10,
        folder='./.database',
        migrate=False,
        fake_migrate=True,
        fake_migrate_all=True,
        check_reserved=['all'],
    )
    return db
