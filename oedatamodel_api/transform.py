
from typing import Optional
from enum import Enum
import jmespath


class OedataFormat(str, Enum):
    raw = "raw"
    json_normalized = "json_normalized"
    json_concrete = "json_concrete"
    csv_normalized = "csv_normalized"
    csv_concrete = "csv_concrete"


def format_data(raw_json, data_format: OedataFormat):
    if data_format == OedataFormat.raw:
        return raw_json
    if data_format == OedataFormat.json_normalized:
        return get_normalized_json(raw_json)


def get_data_indexes(raw_json):
    return [i for i, column in enumerate(raw_json["description"]) if column[0] == "id"]


def get_scenario_data(raw_json, scenario_columns: int):
    scenario_data = {}
    for i in range(scenario_columns):
        column_name = raw_json["description"][i][0]
        # As scenario data is same in every row, we only need first row:
        scenario_data[column_name] = raw_json["data"][0][i]
    return scenario_data


def get_multiple_rows_from_data(raw_json, start: int, end: Optional[int] = None):
    column_names = [column[0] for column in raw_json["description"][start:end]]
    table_data = []
    for row in raw_json["data"]:
        # Skip rows, if "id" column is not set (empty scalars or timeseries):
        if row[start] is None:
            continue
        table_data.append(dict(zip(column_names, row[start:end])))
    return table_data


def get_normalized_json(raw_json):
    table_indexes = get_data_indexes(raw_json)
    scenario = get_scenario_data(raw_json, table_indexes[1])
    data = get_multiple_rows_from_data(raw_json, start=table_indexes[1], end=table_indexes[2])
    timeseries = get_multiple_rows_from_data(raw_json, start=table_indexes[2], end=table_indexes[3])
    scalars = get_multiple_rows_from_data(raw_json, start=table_indexes[3])
    return {"oed_scenario": scenario, "oed_data": data, "oed_scalars": scalars, "oed_timeseries": timeseries, }
