
import datetime as dt
import json
import requests
import warnings
from frictionless import validate_resource, Resource


from oedatamodel_api.settings import OEP_URL, OEP_TOKEN


OEP_TO_FRICTIONLESS_CONVERSION = {
    "bigint": "integer",
    "text": "string",
    "json": "object",
    "decimal": "number",
    "interval": "any",
    "timestamp": "datetime"
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
            'type': 'table',
            'table': table,
            'schema': schema
        },
        "order_by": [
            {
                "type": "column",
                "column": "id",
                "ordering": "desc"
            }
        ],
        "limit": 1
    }
    response = requests.post(f"{OEP_URL}/api/v0/advanced/search", json={"query": query})
    return response.json()['data'][0][0] + 1


def adapt_foreign_keys(data, schema):
    """This method is Modex-specific and a dirty hack"""
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
            "(and its corresponding -output tables)"
        )
    # Checks
    if (
            len(data) != 4 or
            not all([table in data for table in (scenario_table, data_table, scalar_table, timeseries_table)])
    ):
        raise UploadError(
            "Foreign-key adaption is only available for oed_datamodel tables "
            "(and its corresponding -output tables)"
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

    for id_, scalar_row in enumerate(data[scalar_table]):
        scalar_row["id"] = data_id_mapping[scalar_row["id"]]

    for id_, timeseries_row in enumerate(data[timeseries_table]):
        timeseries_row["id"] = data_id_mapping[timeseries_row["id"]]

    return data


def upload_data_to_oep(data, schema):
    def default_serialization(item):
        if isinstance(item, (dt.date, dt.datetime)):
            return item.isoformat()
        return item

    for table, table_data in data.items():
        table_url = f"{OEP_URL}/api/v0/schema/{schema}/tables/{table}/rows/new"
        response = requests.post(
            url=table_url,
            data=json.dumps({"query": table_data}, default=default_serialization),
            headers={
                'Authorization': 'Token %s' % OEP_TOKEN,
                'Content-type': 'application/json',
            }
        )
        if response.status_code != 201:
            raise UploadError(response.text)


def validate_upload_data(data, schema):
    errors = []
    for table, data_dict in data.items():
        # Get datapackage format for each table in data
        meta_url = f"{OEP_URL}/api/v0/schema/{schema}/tables/{table}/meta/"
        metadata = json.loads(requests.get(meta_url).content)
        try:
            oep_schema = metadata["resources"][0]["schema"]
        except (KeyError, IndexError):
            warnings.warn(
                f"Metadata for OEP table '{schema}.{table}' not found or invalid. "
                f"Thus, data could not be validated against table format"
            )
            continue

        # Rewrite datapackage format and validate json (instead of postgresql):
        fl_table_schema = reformat_oep_to_frictionless_schema(oep_schema)
        resource = Resource(
            name=table, profile="tabular-data-resource", data=data_dict, schema=fl_table_schema
        )
        report = validate_resource(resource)
        if report["stats"]["errors"] != 0:
            errors.append(report.to_dict())

    if len(errors) > 0:
        raise ValidationError(errors)


def reformat_oep_to_frictionless_schema(schema):
    # Ignore other fields than 'fields' and 'primaryKey' (i.e. "foreignKeys")
    fields = []
    for field in schema["fields"]:
        if "array" in field["type"]:
            type_ = "array"
        else:
            type_ = OEP_TO_FRICTIONLESS_CONVERSION.get(field["type"], field["type"])
        fields.append({"name": field["name"], "type": type_})
    fl_schema = {
        "fields": fields,
        "primaryKey": schema["primaryKey"]
    }
    return fl_schema
