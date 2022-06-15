import json
import logging

import requests
from redis import Redis
from redis.exceptions import ConnectionError as RedisConnectionError

from oedatamodel_api.settings import REDIS_URL, SOURCES_DIR

OEP_URL = "https://openenergy-platform.org"

redis = Redis.from_url(REDIS_URL)


class OEPDataNotFoundError(Exception):
    """Is raised if data could not be found in OEP"""


class SourceNotFound(Exception):
    """Exception is thrown, if source is not found in folder "sources"."""


def get_data_from_oep(project, source, **params):
    cache_key = f"{source}{f'_{project}' or ''}{'_'.join((f'({k},{v})' for k, v in params.items()))}"
    try:
        cached_data = redis.get(cache_key)
    except RedisConnectionError:
        cached_data = None
    if cached_data:
        return json.loads(cached_data)

    try:
        join = load_source(project, source, params)
    except SourceNotFound:
        raise
    data = {"query": join}
    response = requests.post(f"{OEP_URL}/api/v0/advanced/search", json=data)
    if response.status_code != 200:
        logging.error(
            "Error in data request to OEP", project, source, params, response.text
        )
        raise ConnectionError(response.text)
    response_json = response.json()
    if response_json["content"]["rowcount"] == 0:
        logging.warning(
            "Could not get data from OEP", project, source, params, response.text
        )
        raise OEPDataNotFoundError("Data not found", project, source, params)
    try:
        redis.set(cache_key, response.text)
    except RedisConnectionError:
        pass
    return response_json


def replace_json_placeholders(json_raw, values):
    for k, v in values.items():
        placeholder = f"<{k}>"
        json_raw = json_raw.replace(placeholder, str(v))
    return json_raw


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
    json_with_params = replace_json_placeholders(json_str, params)
    return json.loads(json_with_params)
