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


def get_data_from_oep(source, **params):
    cache_key = source + "_".join(f"({k},{v})" for k, v in params.items())
    try:
        cached_data = redis.get(cache_key)
    except RedisConnectionError:
        cached_data = None
    if cached_data:
        return json.loads(cached_data)
    join = load_source(source, params)
    data = {"query": join}
    response = requests.post(
        OEP_URL + "/api/v0/advanced/search",
        json=data,
    )
    if response.status_code != 200:
        logging.error("Error in data request to OEP", source, params, response.text)
        raise ConnectionError(response.text)
    response_json = response.json()
    if response_json["content"]["rowcount"] == 0:
        logging.warning("Could not get data from OEP", source, params, response.text)
        raise OEPDataNotFoundError("Data not found", source, params)
    try:
        redis.set(cache_key, response.text)
    except RedisConnectionError:
        pass
    return response_json


def replace_json_placeholders(json_raw, values):
    for k, v in values.items():
        placeholder = "<%s>" % k
        json_raw = json_raw.replace(placeholder, str(v))
    return json_raw


def load_source(name, params):
    params = params or {}
    filename = f"{name}.json"
    try:
        with open(SOURCES_DIR / filename, "r") as json_file:
            json_str = json_file.read()
    except OSError:
        raise SourceNotFound(f'Unknown source "{name}".')  # noqa: W0707
    json_with_params = replace_json_placeholders(json_str, params)
    return json.loads(json_with_params)
