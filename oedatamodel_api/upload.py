
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


def get_normalized_attributes():
    data = load_json(OEDATAMODEL_META_DIR / "OEDataModel-normalization-datapackage.json")
    return {
        table: jmespath.search(
            f"resources[?name=='{OEDATAMODEL_SCHEMA}.{table}'] | [0].schema.fields[*].name",
            data
        )
        for table in NORMALIZED_TABLES
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


def upload_csv_from_zip(zip_file):
    tf = tempfile.TemporaryFile()
    tf.write(zip_file.file.read())
    tf.seek(0)
    zfile = zipfile.ZipFile(tf, 'r')

    dfs = {}
    zip_folder_name = zfile.namelist()[0]
    for filename in zfile.namelist()[1:]:
        file = zfile.read(filename)
        table = filename[len(zip_folder_name):-4]
        dfs[table] = read_in_csv_file(io.BytesIO(file), table)
    return upload_dfs(dfs)


def upload_dfs(dfs):
    data, scalar, timeseries = map_concrete_to_normalized_df(dfs["oed_scalar"], dfs["oed_timeseries"])
    normalized_dfs = {
            "oed_scenario": dfs["oed_scenario"],
            "oed_data": data,
            "oed_scalar": scalar,
            "oed_timeseries": timeseries
        }
    filtered_normalized_dfs = adapt_metadata_attributes_and_types(normalized_dfs)
    return upload_normalized_dfs(
        filtered_normalized_dfs,
        schema="model_draft"
    )


def read_in_csv_file(file, table):
    oep_tables = get_oep_tables()
    df = pandas.read_csv(file, sep=";", encoding="cp1250")
    columns = oep_tables[table].columns
    if table in ("oed_scalar", "oed_timeseries"):
        columns += oep_tables["oed_data"].columns
    for column in columns:
        if repr(column.type) in TYPE_CONVERSION:
            df[str(column.name)] = df[str(column.name)].apply(TYPE_CONVERSION[repr(column.type)])
    return df


def map_concrete_to_normalized_df(scalar_df, timeseries_df):
    norm = get_normalized_attributes()
    concrete_data_attrs = set(norm["oed_data"]) - {"type"}
    scalar_data_df = scalar_df[concrete_data_attrs]
    scalar_data_df["type"] = "scalar"
    timeseries_data_df = timeseries_df[concrete_data_attrs]
    timeseries_data_df["type"] = "timeseries"
    data_df = pandas.concat([scalar_data_df, timeseries_data_df], ignore_index=True)
    return data_df, scalar_df, timeseries_df


def adapt_metadata_attributes_and_types(dfs: Dict[str, pandas.DataFrame]):
    norm = get_normalized_attributes()
    for table in NORMALIZED_TABLES:
        dfs[table] = dfs[table][norm[table]]
    return dfs


def upload_normalized_dfs(dfs: Dict[str, pandas.DataFrame], schema: str):
    def set_ids(df, start_id):
        df["id"] = range(start_id, len(df) + start_id)

    def upload_table(table_name, df):
        dtypes = {str(column.name): column.type for column in oep_tables[table_name].columns}
        df.to_sql(
            name=table_name, con=db.engine, schema=schema, if_exists="append", index=False, dtype=dtypes
        )

    db = setup_db_connection()
    oep_tables = get_oep_tables(db)

    # Upload scenario:
    if len(dfs["oed_scenario"]) > 1:
        raise IndexError("Scenarios can only be uploaded one by one")
    scenario_id = get_next_id(db, oep_tables["oed_scenario"])
    scenario = dfs["oed_scenario"]
    set_ids(scenario, scenario_id)
    upload_table("oed_scenario", scenario)

    # Upload data:
    next_id = get_next_id(db, oep_tables["oed_data"])
    data = dfs["oed_data"]
    data["scenario_id"] = scenario_id
    set_ids(data, next_id)
    upload_table("oed_data", data)

    # Upload scalar:
    scalar = dfs["oed_scalar"]
    scalar["id"] = data[data["type"] == "scalar"]["id"]
    upload_table("oed_scalar", scalar)

    # Upload timeseries:
    timeseries = dfs["oed_timeseries"]
    timeseries["id"] = data[data["type"] == "timeseries"]["id"].reset_index(drop=True)
    upload_table("oed_timeseries", timeseries)
    return scenario_id
