"""
Custom mappings are loaded and applied to oedatamodel results
"""

import json

import jmespath

from oedatamodel_api.mapping_default import OedataMapping, map_data
from oedatamodel_api.settings import MAPPINGS_DIR


class MappingNotFound(Exception):
    """Exception is thrown, if custom mapping is not found in folder "mappings"."""


def load_custom_mapping(name):
    """
    Load custom mapping as json/dict from mappings folder.

    Parameters
    ----------
    name: str
        Mapping name (searches for "{name}.json" in mappings folder.

    Raises
    ------
    MappingNotFound
        If custom mapping cannot be found in mappings folder.

    Returns
    -------
    dict
        Custom mapping json/dict.
    """
    filename = f'{name}.json'
    try:
        with open(MAPPINGS_DIR / filename, 'r') as json_file:
            json_data = json.load(json_file)
    except FileNotFoundError:
        raise MappingNotFound(f'Unknown mapping "{name}".')  # noqa: W0707
    return json_data


def apply_custom_mapping(raw_json, name):
    """
    Custom mapping is loaded and applied to raw json/dict.

    Custom mapping can depend on pre-mappings
    (custom or default, last iteration must depend on default mapping,
    i.e. "normalized" or "concrete").
    Depending mappings are recursively applied before current mapping is applied.

    Parameters
    ----------
    raw_json: dict
        Result from OEP to perform custom mapping on.
    name: str
        Custom (must be present in mappings folder) or default
        ("normalized" or "concrete") mapping name.

    Returns
    -------
    dict
        Resulting json/dict after applying all custom/default mappings.
    """
    if name in (m for m in OedataMapping):
        return map_data(raw_json, name)
    mapping = load_custom_mapping(name)
    # Recursively apply base mappings:
    pre_json = apply_custom_mapping(raw_json, mapping['base_mapping'])
    # Recursively apply custom mapping on pre json:
    return iterate_mapping(pre_json, mapping['mapping'])


def iterate_mapping(raw_json, value):
    """
    Recursive function to apply mappings down the mapping tree.

    Parameters
    ----------
    raw_json: dict
        Scenario result or pre-mapped json.
    value: Union[dict, str]
        Either a dict (then next, deeper iteration is done) or a str
        (containing jmespath function to apply on given json).

    Returns
    -------
    Union[dict, str, list]
        Either dict containing next iteration or result from jmespath function
        applied to given json.
    """
    if isinstance(value, dict):
        return {key: iterate_mapping(raw_json, mapping) for key, mapping in value.items()}
    return jmespath.search(value, raw_json)
