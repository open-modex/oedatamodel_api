import datetime as dt
import json
import logging

import requests
from frictionless import Resource, validate_resource

from oedatamodel_api.settings import OEP_URL

logger = logging.getLogger("uvicorn.error")


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
        report = validate_resource(resource)
        if report["stats"]["errors"] != 0:
            errors.append(report.to_dict())
    if errors:
        raise ValidationError(errors)


def get_resources_from_data(data, schema):
    resources = []
    for table, data_source in data.items():
        # Get datapackage format for each table in data
        meta_url = f"{OEP_URL}/api/v0/schema/{schema}/tables/{table}/meta/"
        response = requests.get(meta_url)
        if response.status_code != 200:
            raise UploadError(f"Table '{schema}.{table}' unavailable on OEP platform.")
        metadata = json.loads(response.content)
        try:
            oep_schema = metadata["resources"][0]["schema"]
        except (KeyError, IndexError):
            raise UploadError(f"Table '{schema}.{table}' has no valid metadata.")

        # Rewrite datapackage format and validate json, instead of postgresql:
        fl_table_schema = reformat_oep_to_frictionless_schema(oep_schema)
        if isinstance(data_source, dict):
            resources.append(
                Resource(
                    name=table,
                    profile="tabular-data-resource",
                    data=data_source,
                    schema=fl_table_schema,
                )
            )
        else:
            resources.append(
                Resource(
                    name=table,
                    profile="tabular-data-resource",
                    source=data_source,
                    schema=fl_table_schema,
                    format="csv",
                )
            )
    return resources


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
            field_data["floatNumber"] = "True"
        fields.append(field_data)
    return {
        "fields": fields,
        "primaryKey": schema["primaryKey"],
    }
