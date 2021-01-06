"""
Custom mappings are loaded and applied to oedatamodel results
"""

from parse import parse
import json
import datetime as dt
from itertools import groupby, repeat

import jmespath
from jmespath import functions, exceptions

from oedatamodel_api.mapping_default import OedataMapping, map_data
from oedatamodel_api.settings import MAPPINGS_DIR


DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"
RESOLUTION_REGEX = "P{days:1d}DT{hours:2d}H{minutes:2d}M{seconds:2d}S"


class CustomFunctions(functions.Functions):
    """
    From: https://github.com/jmespath/jmespath.site/issues/17#issuecomment-198111810
    ----------------
    Custom functions extend jmespath core functionality. They help to process
    json data and enable to apply a custom mapping on the json data (See apply_custom_mapping).

    Currently available custom functions are:
    - repeat
    - items
    - zip
    - to object
    - unique
    - exclude
    - group by
        group_by allows for the expref to be either a number of
        a string, so we have some special logic to handle this.
        We evaluate the first array element and verify that it's
        either a string of a number.  We then create a key function
        that validates that type, which requires that remaining array
        elements resolve to the same type as the first element.
    - group by dict
         group_dict_by allows for the expref to be either a number of
        a string, so we have some special logic to handle this.
        We evaluate the first array element and verify that it's
        either a string of a number.  We then create a key function
        that validates that type, which requires that remaining array
        elements resolve to the same type as the first element.
    """

    @functions.signature({'types': ['object', 'string']}, {'types': ['number']})
    def _func_repeat(self, arg, times):
        return list(repeat(arg, times))

    @functions.signature({'types': ['object']})
    def _func_items(self, arg):
        return list(map(list, arg.items()))

    @functions.signature({'types': ['array'], 'variadic': True})
    def _func_zip(self, *arguments):
        return list(map(list, zip(*arguments)))

    @functions.signature({'types': ['array'], 'variadic': True})
    def _func_zip_multi(self, *arguments):
        return list(map(list, zip(*arguments)))

    @functions.signature({'types': ['array']})
    def _func_to_object(self, pairs):
        return dict(pairs)

    @functions.signature({'types': ['array']})
    def _func_merge_array(self, array):
        d = {}
        for a in array:
            d.update(a)
        return d

    @functions.signature({'types': ['object']}, {'types': ['object', 'string', 'array', 'number']})
    def _func_fill_na(self, d, value):
        return {k: value if v is None else v for k, v in d.items()}

    @functions.signature({'types': ['string']}, {'types': ['string']}, {'types': ['string']})
    def _func_timerange(self, start, end, resolution):
        dt_start = dt.datetime.strptime(start, DATETIME_FORMAT)
        dt_end = dt.datetime.strptime(end, DATETIME_FORMAT)
        res_parsed = parse(RESOLUTION_REGEX, resolution)
        delta = dt.timedelta(
            days=res_parsed["days"],
            hours=res_parsed["hours"],
            minutes=res_parsed["minutes"],
            seconds=res_parsed["seconds"]
        )
        timeindex = []
        current_index = dt_start
        while current_index <= dt_end:
            timeindex.append(current_index)
            current_index += delta
        return timeindex

    @functions.signature(
        {'types': ['object']}, {'types': ['string']}, {'types': ['object', 'string', 'array', 'number','null']})
    def _func_set(self, d, key, value):
        d_new = d.copy()
        d_new[key] = value
        return d_new

    @functions.signature(
        {'types': ['object']}, {'types': ['string']}, {'types': ['object', 'string', 'array', 'number']}, {'types': ['object', 'string', 'array', 'number']})
    def _func_set_combi(self, d, key, value1, value2):
        d_new = d.copy()
        d_new[key] = value1 + '_' + value2
        return d_new
        
    @functions.signature({'types': ['object']})
    def _func_unpack_dict_series(self, d):
        new_list = []
        series_length = len(list(d.values())[0])
        for i in range(series_length):
            new_list.append({k: d[k][i] for k in d.keys()})
        return new_list

    @functions.signature({'types': ['array']})
    def _func_unique(self, args):
        if len(args) > 0 and isinstance(args[0], dict):
            return [dict(s) for s in set(frozenset(d.items()) for d in args)]
        return list(dict.fromkeys(args))

    @functions.signature({'types': ['object']}, {'types': ['array']})
    def _func_exclude(self, arg, excludes):
        return {k: v for k, v in arg.items() if k not in excludes}

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
    except (FileNotFoundError, OSError):
        raise MappingNotFound(f'Unknown mapping "{name}".')  # noqa: W0707
    return json_data


def apply_custom_mapping(raw_json: dict, mapping: str):
    """
    Custom mapping is (loaded and) applied to raw json/dict.

    Custom mapping can depend on pre-mappings
    (custom or default, last iteration must depend on default mapping,
    i.e. "normalized" or "concrete").
    Depending mappings are recursively applied before current mapping is applied.

    Parameters
    ----------
    raw_json: dict
        Result from OEP to perform custom mapping on.
    mapping: str
        Custom mapping (either name of predefined mapping or mapping json) which shall be applied

    Returns
    -------
    dict
        Resulting json/dict after applying all custom/default mappings.
    """
    if mapping in (m for m in OedataMapping):
        return map_data(raw_json, mapping)
    try:
        mapping_json = load_custom_mapping(mapping)
    except MappingNotFound:
        mapping_json = json.loads(mapping)
    # Recursively apply base mappings if one exists:
    if mapping_json['base_mapping'] == "":
        pre_json = raw_json
    else:
        pre_json = apply_custom_mapping(raw_json, mapping_json['base_mapping'])
    # Recursively apply custom mapping on pre json:
    return iterate_mapping(pre_json, mapping_json['mapping'])


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
