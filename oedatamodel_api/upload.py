import datetime as dt
import json
import logging
import re

import frictionless
import requests
from frictionless import Dialect, Resource, Schema, transform, steps
from frictionless.formats import CsvControl

from oedatamodel_api.settings import OEP_URL

logger = logging.getLogger("uvicorn.error")

DEFAULT_CSV_DELIMITER = ";"
DEFAULT_HEADER_ROWS = [
    1
]  # Otherwise frictionless sometimes "detects" multiple row header and validation crashes

OEP_TO_FRICTIONLESS_CONVERSION = {
    "int": "integer",
    "bigint": "integer",
    "text": "string",
    "json": "object",
    "decimal": "number",
    "interval": "any",
    "timestamp": "datetime",
    "float": "number",
}


class ValidationError(Exception):
    """Exception if validation of datapackage fails"""


class UploadError(Exception):
    """Exception if upload to OEP fails"""


def get_next_id(table, schema):
    query = {
        "fields": [
            "id",
        ],
        "from": {
            "type": "table",
            "table": table,
            "schema": schema,
        },
        "order_by": [
            {
                "type": "column",
                "column": "id",
                "ordering": "desc",
            },
        ],
        "limit": 1,
    }
    response = requests.post(f"{OEP_URL}/api/v0/advanced/search", json={"query": query})
    return response.json()["data"][0][0] + 1


def adapt_foreign_keys(data, schema):
    # FIXME: This method is Modex-specific and a dirty hack
    if "oed_scenario" in data:
        scenario_table = "oed_scenario"
        data_table = "oed_data"
        scalar_table = "oed_scalar"
        timeseries_table = "oed_timeseries"
    elif "oed_scenario_output" in data:
        scenario_table = "oed_scenario_output"
        data_table = "oed_data_output"
        scalar_table = "oed_scalar_output"
        timeseries_table = "oed_timeseries_output"
    else:
        raise UploadError(
            "Foreign-key adaption is only available for oed_datamodel tables "
            "(and its corresponding -output tables)",
        )
    # Checks
    if len(data) != 4 or any(
        table not in data
        for table in (scenario_table, data_table, scalar_table, timeseries_table)
    ):
        raise UploadError(
            "Foreign-key adaption is only available for oed_datamodel tables "
            "(and its corresponding -output tables)",
        )
    if len(data[scenario_table]) > 1:
        raise UploadError("ForeignKey adaption only works for one scenario")

    scenario_id = get_next_id(scenario_table, schema)
    data[scenario_table][0]["id"] = scenario_id

    data_id = get_next_id(data_table, schema)
    data_id_mapping = {}  # store data ids and map to scalars and ts later
    for id_, data_row in enumerate(data[data_table]):
        new_id = data_id + id_
        data_id_mapping[data_row["id"]] = new_id
        data_row["id"] = new_id
        data_row["scenario_id"] = scenario_id

    for scalar_row in data[scalar_table]:
        scalar_row["id"] = data_id_mapping[scalar_row["id"]]

    for timeseries_row in data[timeseries_table]:
        timeseries_row["id"] = data_id_mapping[timeseries_row["id"]]

    return data, scenario_id


def upload_data_to_oep(data, schema, token):
    def default_serialization(item):
        return item.isoformat() if isinstance(item, (dt.date, dt.datetime)) else item

    for table, table_data in data.items():
        table_url = f"{OEP_URL}/api/v0/schema/{schema}/tables/{table}/rows/new"
        response = requests.post(
            url=table_url,
            data=json.dumps({"query": table_data}, default=default_serialization),
            headers={
                "Authorization": "Token %s" % token,
                "Content-type": "application/json",
            },
        )
        if response.status_code != 201:
            raise UploadError(response.text)
        logger.debug(f"Successfully uploaded table '{table}'")


def validate_resources(resources):
    errors = []
    for resource in resources:
        report = resource.validate()
        if report.stats["errors"] != 0:
            errors.append(report.to_dict())
    if errors:
        raise ValidationError(errors)


def get_resources_from_data(data, metadata):
    resources = []
    for table, data_source in data.items():
        table_metadata = metadata[table]
        oep_schema = table_metadata["resources"][0]["schema"]

        # Rewrite datapackage format and validate json, instead of postgresql:
        fl_table_schema = reformat_oep_to_frictionless_schema(oep_schema)
        schema = Schema.from_descriptor(fl_table_schema)
        if isinstance(data_source, dict):
            resources.append(
                Resource(
                    name=table,
                    profile="tabular-data-resource",
                    data=data_source,
                    schema=schema,
                )
            )
        else:
            fixed_data = fix_json_encoding(data_source)
            try:
                delimiter = table_metadata["resources"][0]["dialect"]["delimiter"]
            except KeyError:
                delimiter = DEFAULT_CSV_DELIMITER
            csv_control = CsvControl(delimiter=delimiter)
            dialect = Dialect(header_rows=DEFAULT_HEADER_ROWS, controls=[csv_control])
            resources.append(
                Resource(
                    name=table,
                    profile="tabular-data-resource",
                    source=fixed_data,
                    schema=schema,
                    format="csv",
                    dialect=dialect,
                )
            )
    return resources


def adapt_primary_keys(resource: frictionless.Resource, table: str, schema: str) -> frictionless.Resource:
    """
    Adapts primary keys in column "id" to next free number in OEP table
    """
    def inc_pk(current_pk):
        # Conversion to int is necessary, otherwise frictionless transformation gets None due to wrong type.
        return int(next_id + current_pk - min_id)

    next_id = get_next_id(table, schema)
    min_id = resource.to_pandas().index.min()
    return transform(
        resource,
        steps=[
            steps.table_normalize(),
            steps.cell_convert(field_name='id', function=inc_pk),
        ],
    )


def fix_json_encoding(data: bytes) -> bytes:
    """
    Fixes JSON cells in CSv data

    Replaces single quotes with two double quotes and quotes whole JSON.
    Afterwards, JSON can be read in by frictionless.

    Parameters
    ----------
    data: bytes
        Raw input data from CSV

    Returns
    -------
    bytes
        Data with fixed JSONs
    """
    data_str = data.decode("utf-8")
    data_str = data_str.replace("\'", '\"\"')
    data_str = re.sub('(?<!"){', '"{', data_str)
    data_str = re.sub('}(?!")', '}"', data_str)
    return data_str.encode()


def reformat_oep_to_frictionless_schema(schema):
    # Ignore other fields than 'fields' and 'primaryKey' (i.e. "foreignKeys")
    fields = []
    for field in schema["fields"]:
        if "array" in field["type"]:
            type_ = "array"
        else:
            type_ = OEP_TO_FRICTIONLESS_CONVERSION.get(field["type"], field["type"])
        field_data = {"name": field["name"], "type": type_}
        if field["type"] == "float":
            field_data["floatNumber"] = True
        fields.append(field_data)
    return {
        "fields": fields,
        "primaryKey": schema["primaryKey"],
    }
