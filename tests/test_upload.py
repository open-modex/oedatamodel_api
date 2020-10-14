
from oem2orm.oep_oedialect_oem2orm import setup_db_connection
from oedatamodel_api.settings import NORMALIZED_TABLES, CONCRETE_TABLES
from oedatamodel_api import upload


def test_oep_tables():
    tables = upload.get_oep_tables()
    assert len(tables) == 4
    assert all(key in tables.keys() for key in NORMALIZED_TABLES)


def test_next_id():
    db = setup_db_connection()
    tables = upload.get_oep_tables(db)
    assert isinstance(upload.get_next_id(db, tables["oed_scenario"]), int)


def test_map_dfs():
    dfs = upload.read_in_excel_sheets(
        "scenario_scalar_timeseries_less.xlsx",
        sheets=("scenario", "scalar", "timeseries")
    )
    assert len(dfs) == 3
    data, scalar, timeseries = upload.map_concrete_to_normalized_df(dfs["scalar"], dfs["timeseries"])
    assert len(scalar) == 71
    assert len(scalar.columns) == 3
    assert len(timeseries) == 10
    assert len(timeseries.columns) == 5
    assert len(data) == 81
    assert len(data.columns) == 14


def test_upload_normalized_dfs():
    sheets = ("scenario", "scalar", "timeseries")
    dfs = upload.read_in_excel_sheets(
        "scenario_scalar_timeseries_less.xlsx",
        sheets=sheets,
        sheet_table_map=dict(zip(sheets, CONCRETE_TABLES))
    )
    data, scalar, timeseries = upload.map_concrete_to_normalized_df(dfs["scalar"], dfs["timeseries"])
    normalized_dfs = {
            "oed_scenario": dfs["scenario"],
            "oed_data": data,
            "oed_scalar": scalar,
            "oed_timeseries": timeseries
        }
    filtered_normalized_dfs = upload.adapt_metadata_attributes_and_types(normalized_dfs)
    upload.upload_normalized_dfs(
        filtered_normalized_dfs,
        schema="model_draft"
    )


def test_adapt_metadata():
    sheets = ("scenario", "scalar", "timeseries")
    dfs = upload.read_in_excel_sheets(
        "scenario_scalar_timeseries_less.xlsx",
        sheets=sheets,
        sheet_table_map=dict(zip(sheets, CONCRETE_TABLES))
    )
    data, scalar, timeseries = upload.map_concrete_to_normalized_df(dfs["scalar"], dfs["timeseries"])
    normalized_dfs = {
        "oed_scenario": dfs["scenario"],
        "oed_data": data,
        "oed_scalar": scalar,
        "oed_timeseries": timeseries
    }
    filtered_dfs = upload.adapt_metadata_attributes_and_types(normalized_dfs)
    region = filtered_dfs["oed_scenario"]["region"][0]
    assert isinstance(region, list)
    assert region[0] == "DE"
    series = filtered_dfs["oed_timeseries"]["series"][0]
    assert isinstance(series, list)
    assert isinstance(series[0], float)


def test_query_attributes():
    attributes = upload.get_normalized_attributes()
    assert len(attributes) == 4
    assert len(attributes["oed_scenario"]) == 6
    assert len(attributes["oed_data"]) == 14
    assert len(attributes["oed_scalar"]) == 3
    assert len(attributes["oed_timeseries"]) == 5
