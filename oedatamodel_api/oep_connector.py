import json

import requests
from redis import Redis
from redis.exceptions import ConnectionError as RedisConnectionError

from oedatamodel_api.settings import REDIS_URL, SOURCES_DIR, logger

OEP_URL = "https://openenergy-platform.org"

redis = Redis.from_url(REDIS_URL)


class OEPDataNotFoundError(Exception):
    """Is raised if data could not be found in OEP"""


class SourceNotFound(Exception):
    """Exception is thrown, if source is not found in folder "sources"."""


def get_data_from_oep(project, source, **params):
    try:
        tables = load_source(project, source, params)
    except SourceNotFound:
        raise
    if "from" in tables:  # This detects a single table
        return query_oep(tables, project, source, **params)
    else:
        return {
            key: query_oep(table, project, source, key, **params)
            for key, table in tables.items()
        }


def query_oep(query, project, source, key=None, **params):
    cache_key = f"{source}{f'_{project}' or ''}{f'_{key}' or ''}{'_'.join((f'({k},{v})' for k, v in params.items()))}"
    try:
        cached_data = redis.get(cache_key)
    except RedisConnectionError:
        cached_data = None
    if cached_data:
        logger.info(f"Using cached data with {cache_key=}")
        return json.loads(cached_data)

    data = {"query": query}
    response = requests.post(f"{OEP_URL}/api/v0/advanced/search", json=data)
    if response.status_code != 200:
        logger.error(
            "Error in data request to OEP", project, source, params, response.text
        )
        raise ConnectionError(response.text)
    response_json = response.json()
    if response_json["content"]["rowcount"] == 0:
        logger.warning(
            "Could not get data from OEP", project, source, params, response.text
        )
        raise OEPDataNotFoundError("Data not found", project, source, params)
    try:
        redis.set(cache_key, response.text)
    except RedisConnectionError:
        pass
    return response_json


def set_predefined_parameters(data_str: str, parameters: dict):
    """
    Replaces parameters defined in source file by query parameters

    Parameters
    ----------
    data_str: str
        Source string
    parameters: dict
        Query parameters

    Returns
    -------
    str:
        Source string with placeholders replaced by parameters
    """
    params = {k: v for k, v in parameters.items()}
    for k in list(params.keys()):
        placeholder = f"<{k}>"
        if placeholder not in data_str:
            continue
        v = params.pop(k)
        data_str = data_str.replace(placeholder, str(v))
    return data_str


def set_dynamic_parameters(source_query, parameters):
    """
    Adds where clause for each query parameter

    Parameters
    ----------
    source_query: dict
        Source as json/dictionary
    parameters: dict
        Query parameters

    Returns
    -------
    str:
        Source dictionary with additional where clauses for each parameter
    """
    if "from" not in source_query:
        return source_query
    if "where" not in source_query:
        source_query["where"] = []
    if isinstance(source_query["where"], dict):
        source_query["where"] = [source_query["where"]]
    for parameter, value in parameters.items():
        source_query["where"].append(
            {
                "operands": [{"column": parameter, "type": "column"}, value],
                "operator": "=",
                "type": "operator",
            }
        )
    return source_query


def load_source(project, name, params):
    params = params or {}
    filename = f"{name}.json"
    source_path = (
        SOURCES_DIR / project / filename if project else SOURCES_DIR / filename
    )
    try:
        with open(source_path, "r") as json_file:
            json_str = json_file.read()
    except OSError as e:
        raise SourceNotFound(f'Unknown source "{name}".') from e
    json_with_params = set_predefined_parameters(json_str, params)
    source_query = json.loads(json_with_params)
    source_query = set_dynamic_parameters(source_query, params)
    return source_query
