from pydal import Field


def define_tables(db):
    """Defines the project tables using pyDAL.

    Note 1: On the application first run there will be created a 'sql.log' file
    in the project root folder containing the 'CREATE TABLE' statements

    Note 2: as pyDAL does not support field indexes to be declared in the
    'Field' object, they will need to be created manually. The fields that
    needs indexing will have the "# needs index" comment besides it.

    Args:
        db (DAL): pyDAL connection object
    """

    db.define_table(
        'city',
        Field('name', 'string', length=40, notnull=True, required=True)
    )

    db.define_table(
        'tech',
        Field('name', 'string', length=40, notnull=True, required=True) 
    )

    db.define_table(
        'candidate',
        Field('city_id', 'integer', 'reference city'),
        # For the years experience fields it is a good idea to create a
        # composite index
        Field('years_experience_min', 'integer', default=0),  # needs index
        Field('years_experience_max', 'integer', default=99),  # needs index
    )

    db.define_table(
        'candidate_tech_reference',
        Field('candidate_id', 'integer', 'reference candidate', notnull=True,
              required=True),
        Field('tech_id', 'integer', 'reference tech', notnull=True,
              required=True),
        Field('is_main_tech', 'boolean', default=False),
    )
