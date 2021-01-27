from elasticsearch import Elasticsearch
from .. import settings

ELASTIC_HOST = settings.ELASTIC_HOST
ELASTIC_USERNAME = settings.ELASTIC_USERNAME
ELASTIC_PASSWORD = settings.ELASTIC_PASSWORD


def get_elastic(): 
    if ELASTIC_HOST == 'localhost':
        es = Elasticsearch()
    else:
        es = Elasticsearch(
            [ELASTIC_HOST],
            http_auth=(
                ELASTIC_USERNAME,
                ELASTIC_PASSWORD
            ),
            scheme="https",
            port=443,
        )
    return es


def get_elastic_credentials():
    return ELASTIC_USERNAME, ELASTIC_PASSWORD


def get_elastic_base_url():
    if ELASTIC_HOST == 'localhost':
        httpsElastic = f"http://{ELASTIC_HOST}:9200/"
    else:
        httpsElastic = f"https://{ELASTIC_HOST}/"
    return httpsElastic
