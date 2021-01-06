
import csv
import io
import zipfile
import tempfile
import json
import pandas
import jmespath
from typing import Dict
from sqlalchemy.orm import sessionmaker
from sqlalchemy import desc
from sqlalchemy.dialects.postgresql import ARRAY, JSON, FLOAT, TEXT

from oem2orm.oep_oedialect_oem2orm import setup_db_connection, collect_tables_from_oem, load_json

from oedatamodel_api.mapping_custom import apply_custom_mapping
from oedatamodel_api.settings import OEDATAMODEL_META_DIR, UPLOAD_DIR, NORMALIZED_TABLES, OEDATAMODEL_SCHEMA


TYPE_CONVERSION = {
    repr(ARRAY(FLOAT)): lambda x: list(map(float, json.loads(x.replace('"', '"""').replace("'", '"').replace(";", ",")))),
    repr(ARRAY(TEXT)): lambda x: json.loads(x.replace('"', '"""').replace("'", '"')),
    repr(JSON): lambda x: json.loads(x.replace('"', '"""').replace("'", '"'))
}


def get_oep_tables(db=None):
    db = db or setup_db_connection()
    tables = collect_tables_from_oem(db, OEDATAMODEL_META_DIR)
    return {table.name: table for table in tables}


def get_next_id(db, table):
    Session = sessionmaker(bind=db.engine)
    session = Session()
    row = session.query(table).order_by(desc("id")).first()
    if row is None:
        return 1
    else:
        return row.id + 1


def get_normalized_attributes(input_data):
    if input_data:
        data = load_json(OEDATAMODEL_META_DIR / "OEDataModel-normalization-datapackage.json")
    else:
        data = load_json(OEDATAMODEL_META_DIR / "OEDataModel-output-normalization-datapackage.json")
    tables = NORMALIZED_TABLES if input_data else [f"{t}_output" for t in NORMALIZED_TABLES]
    return {
        table: jmespath.search(
            f"resources[?name=='{OEDATAMODEL_SCHEMA}.{table}'] | [0].schema.fields[*].name",
            data
        )
        for table in tables
    }


def read_in_excel_sheets(filename, sheets, sheet_table_map=None):
    sheet_table_map = sheet_table_map or {}
    oep_tables = get_oep_tables()
    dfs = {}
    for sheet in sheets:
        table = sheet_table_map.get(sheet, sheet)
        df = pandas.read_excel(UPLOAD_DIR / filename, sheet_name=sheet)
        columns = oep_tables[table].columns
        if table in ("oed_scalar", "oed_timeseries"):
            columns += oep_tables["oed_data"].columns
        for column in columns:
            if repr(column.type) in TYPE_CONVERSION:
                df[str(column.name)] = df[str(column.name)].apply(TYPE_CONVERSION[repr(column.type)])
        dfs[sheet] = df
    return dfs


def upload_csv_from_folder(folder):
    dfs = {}
    fullpath = UPLOAD_DIR / folder
    for file in fullpath.iterdir():
        table = file.name[:-4]
        dfs[table] = read_in_csv_file(file, table)
    return upload_dfs(dfs)


def read_zip(zip_file):
    tf = tempfile.TemporaryFile()
    tf.write(zip_file.file.read())
    tf.seek(0)
    return zipfile.ZipFile(tf, 'r')


def upload_csv_from_zip(zip_file):
    zfile = read_zip(zip_file)
    dfs = {}
    for filename in zfile.namelist():
        csvfile = zfile.read(filename)
        table = filename[:-4]
        dfs[table] = read_in_csv_file(io.BytesIO(csvfile), table)
    return upload_dfs(dfs)


def get_mapped_json_from_zip(zip_file, mapping):
    def read_value(raw_str):
        try:
            return json.loads(raw_str)
        except json.JSONDecodeError:
            if raw_str.startswith("[") and raw_str.endswith("]"):
                return raw_str.strip("""[]"'""").split(",")
            else:
                return raw_str

    zfile = read_zip(zip_file)
    json_data = {}
    for filename in zfile.namelist():
        table = filename[:-4]
        with zfile.open(filename, 'r') as csvfile:
            reader = csv.DictReader(io.TextIOWrapper(csvfile), delimiter=";")
            json_data[table] = [{k: read_value(v) for k, v in row.items()} for row in reader]
    return apply_custom_mapping(json_data, mapping)


def create_dfs_from_json(json_data):
    def dump_json(d):
        if d == "":
            return None
        else:
            json.dumps(d)

    oep_tables = get_oep_tables()
    dfs = {}
    for table, data in json_data.items():
        columns = oep_tables[table].columns
        if table in ("oed_scalar", "oed_timeseries"):
            columns += oep_tables["oed_data"].columns
        elif table in ("oed_scalar_output", "oed_timeseries_output"):
            columns += oep_tables["oed_data_output"].columns
        columns = [column for column in columns if str(column.name) != "type"]
        dfs[table] = pandas.DataFrame(
            [
                {
                    str(column.name): dump_json(row[str(column.name)])
                    if repr(column.type) == "JSON()" else row[str(column.name)]
                    for column in columns
                }
                for row in data
            ]
        )
    return dfs


def upload_dfs(dfs):
    input_data = True
    if "oed_scalar" in dfs:
        data, scalar, timeseries = map_concrete_to_normalized_df(dfs["oed_scalar"], dfs["oed_timeseries"])
        normalized_dfs = {
                "oed_scenario": dfs["oed_scenario"],
                "oed_data": data,
                "oed_scalar": scalar,
                "oed_timeseries": timeseries
            }
    elif "oed_scalar_output" in dfs:
        input_data = False
        data, scalar, timeseries = map_concrete_to_normalized_df(
            dfs["oed_scalar_output"], dfs["oed_timeseries_output"], input_data=input_data)
        normalized_dfs = {
            "oed_scenario_output": dfs["oed_scenario_output"],
            "oed_data_output": data,
            "oed_scalar_output": scalar,
            "oed_timeseries_output": timeseries
        }
    else:
        raise KeyError("Unknown tables")
    filtered_normalized_dfs = adapt_metadata_attributes_and_types(normalized_dfs, input_data)
    return upload_normalized_dfs(
        filtered_normalized_dfs,
        schema="model_draft",
        input_data=input_data
    )


def read_in_csv_file(file, table):
    oep_tables = get_oep_tables()
    df = pandas.read_csv(file, sep=";", encoding="cp1250")
    columns = oep_tables[table].columns
    if table in ("oed_scalar", "oed_timeseries"):
        columns += oep_tables["oed_data"].columns
    elif table in ("oed_scalar_output", "oed_timeseries_output"):
        columns += oep_tables["oed_data_output"].columns
    for column in columns:
        if repr(column.type) in TYPE_CONVERSION:
            df[str(column.name)] = df[str(column.name)].apply(TYPE_CONVERSION[repr(column.type)])
    return df


def map_concrete_to_normalized_df(scalar_df, timeseries_df, input_data=True):
    norm = get_normalized_attributes(input_data)
    data_table_name = "oed_data" if input_data else "oed_data_output"
    concrete_data_attrs = set(norm[data_table_name]) - {"type"}
    try:
        scalar_data_df = scalar_df[concrete_data_attrs]
    except KeyError as e:
        raise KeyError("Missing key in scalars", str(e))
    scalar_data_df["type"] = "scalar"
    try:
        timeseries_data_df = timeseries_df[concrete_data_attrs]
    except KeyError as e:
        raise KeyError("Missing key in timeseries", str(e))
    timeseries_data_df["type"] = "timeseries"
    data_df = pandas.concat([scalar_data_df, timeseries_data_df], ignore_index=True)
    return data_df, scalar_df, timeseries_df


def adapt_metadata_attributes_and_types(dfs: Dict[str, pandas.DataFrame], input_data=True):
    norm = get_normalized_attributes(input_data)
    tables = NORMALIZED_TABLES if input_data else [f"{t}_output" for t in NORMALIZED_TABLES]
    for table in tables:
        dfs[table] = dfs[table][norm[table]]
    return dfs


def upload_normalized_dfs(dfs: Dict[str, pandas.DataFrame], schema: str, input_data: bool):
    def set_ids(df, start_id):
        df["id"] = range(start_id, len(df) + start_id)

    def upload_table(table_name, df):
        dtypes = {str(column.name): column.type for column in oep_tables[table_name].columns}
        df.to_sql(
            name=table_name, con=db.engine, schema=schema, if_exists="append", index=False, dtype=dtypes
        )

    db = setup_db_connection()
    oep_tables = get_oep_tables(db)

    table_names = {
        "scenario": "oed_scenario",
        "data": "oed_data",
        "scalar": "oed_scalar",
        "timeseries": "oed_timeseries"
    }
    if not input_data:
        table_names = {k: f"{v}_output" for k, v in table_names.items()}

    # Upload scenario:
    if len(dfs[table_names["scenario"]]) > 1:
        raise IndexError("Scenarios can only be uploaded one by one")
    scenario_id = get_next_id(db, oep_tables[table_names["scenario"]])
    scenario = dfs[table_names["scenario"]]
    set_ids(scenario, scenario_id)
    upload_table(table_names["scenario"], scenario)

    # Upload data:
    next_id = get_next_id(db, oep_tables[table_names["data"]])
    data = dfs[table_names["data"]]
    data["scenario_id"] = scenario_id
    set_ids(data, next_id)
    upload_table(table_names["data"], data)

    # Upload scalar:
    scalar = dfs[table_names["scalar"]]
    scalar["id"] = data[data["type"] == "scalar"]["id"]
    upload_table(table_names["scalar"], scalar)

    # Upload timeseries:
    timeseries = dfs[table_names["timeseries"]]
    timeseries["id"] = data[data["type"] == "timeseries"]["id"].reset_index(drop=True)
    upload_table(table_names["timeseries"], timeseries)
    return scenario_id
