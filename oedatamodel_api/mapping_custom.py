import json

from oedatamodel_api.mapping_default import OedataMapping, map_data
from oedatamodel_api.settings import MAPPINGS_DIR


class MappingNotFound(Exception):
    """Exception is thrown, if custom mapping is not found in folder "mappings"."""


def load_custom_mapping(name):
    filename = f'{name}.json'
    try:
        with open(MAPPINGS_DIR / filename, 'r') as json_file:
            json_data = json.load(json_file)
    except FileNotFoundError:
        raise MappingNotFound(f'Unknown mapping "{name}".')
    return json_data


def apply_custom_mapping(raw_json, name):
    if name in (m for m in OedataMapping):
        return map_data(raw_json, name)
    mapping = load_custom_mapping(name)
    # Recursively apply base mappings:
    pre_json = apply_custom_mapping(raw_json, mapping['base_mapping'])

    return pre_json
