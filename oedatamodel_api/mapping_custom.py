"""
Custom mappings are loaded and applied to oedatamodel results
"""

import json
from itertools import groupby

import jmespath
from jmespath import functions, exceptions

from oedatamodel_api.mapping_default import OedataMapping, map_data
from oedatamodel_api.settings import MAPPINGS_DIR


class CustomFunctions(functions.Functions):
    """From: https://github.com/jmespath/jmespath.site/issues/17#issuecomment-198111810"""

    @functions.signature({'types': ['object']})
    def _func_items(self, arg):
        return list(map(list, arg.items()))

    @functions.signature({'types': ['array'], 'variadic': True})
    def _func_zip(self, *arguments):
        return list(map(list, zip(*arguments)))

    @functions.signature({'types': ['array']})
    def _func_to_object(self, pairs):
        return dict(pairs)

    @functions.signature({'types': ['array']})
    def _func_unique(self, *args):
        return list(dict.fromkeys(*args))

    @functions.signature({'types': ['array']}, {'types': ['expref']})
    def _func_group_by(self, array_object, expref):
        if not array_object:
            return array_object
        # group_by allows for the expref to be either a number of
        # a string, so we have some special logic to handle this.
        # We evaluate the first array element and verify that it's
        # either a string of a number.  We then create a key function
        # that validates that type, which requires that remaining array
        # elements resolve to the same type as the first element.
        lookup = array_object[0]
        required_type = self._convert_to_jmespath_type(
            type(expref.visit(expref.expression, lookup)).__name__)
        if required_type not in ['number', 'string']:
            raise exceptions.JMESPathTypeError(
                'group_by', lookup, required_type, ['string', 'number'])
        keyfunc = self._create_key_func(expref, [required_type], 'group_by')
        return {k: list(g) for k, g in groupby(array_object, key=keyfunc)}

    @functions.signature({'types': ['object']}, {'types': ['expref']})
    def _func_group_dict_by(self, arg, expref):
        if not arg:
            return arg
        # group_dict_by allows for the expref to be either a number of
        # a string, so we have some special logic to handle this.
        # We evaluate the first array element and verify that it's
        # either a string of a number.  We then create a key function
        # that validates that type, which requires that remaining array
        # elements resolve to the same type as the first element.
        lookup = list(list(arg.items())[0])
        required_type = self._convert_to_jmespath_type(
            type(expref.visit(expref.expression, lookup)).__name__)
        if required_type not in ['number', 'string']:
            raise exceptions.JMESPathTypeError(
                'group_by', lookup, required_type, ['string', 'number'])
        keyfunc = self._create_key_func(expref, [required_type], 'group_by')
        # Jmespath works only on lists, not tuples:
        unpacked_dict = [[k, v] for k, v in arg.items()]
        return {
            grouper: {k: v for k, v in list(grouping)}
            for grouper, grouping in groupby(unpacked_dict, key=keyfunc)
        }


jmespath_options = jmespath.Options(custom_functions=CustomFunctions())


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
    return jmespath.search(value, raw_json, options=jmespath_options)
