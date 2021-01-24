import os

"""
    This file contains all variables and environment variables needed for the
    project to run
"""

DB_HOST = os.getenv('DB_HOST', 'not_informed')
DB_NAME = os.getenv('DB_NAME', 'not_informed')
DB_USER = os.getenv('DB_USER', 'not_informed')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'not_informed')
