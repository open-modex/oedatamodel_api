
import json
import pathlib
from oedatamodel_api import upload

TEST_FOLDER = pathlib.Path(__file__).parent
TEST_DATA_FOLDER = TEST_FOLDER / "test_data"

METADATA_FILENAME = TEST_DATA_FOLDER / "metadata.json"

with METADATA_FILENAME.open("r", encoding="utf-8") as metadatafile:
    METADATA = json.load(metadatafile)


def test_adapt_pks():
    filename = TEST_DATA_FOLDER / "valid_json.csv"
    with filename.open("rb") as csvfile:
        data = {"table": csvfile.read()}
    resource = upload.get_resources_from_data(data, {"table": METADATA})[0]
    upload.get_next_id = lambda x, y: 55
    adapted_resource = upload.adapt_primary_keys(resource, "table", "schema")
    assert adapted_resource.to_pandas().index[0] == 55

def test_fix_json():
    valid_json = b'1;global;2020;[60,80];[850];[2,3];[3.8,8.2];[65];[30];[20,30];;v1;;"{""operational_temperature"":""akbar_review_2020"",""investment_cost"":""sterner_power--gas_2021"",""fixed_cost"":""rego_de_vasconcelos_recent_2019"",""electricity_demand"":""rego_de_vasconcelos_recent_2019"",""process_efficiency"":""akbar_review_2020"",""operational_lifetime"":""gotz_renewable_2016"",""minimal_load"":""akbar_review_2020""}";'
    invalid_json = b"1;global;2020;[60,80];[850];[2,3];[3.8,8.2];[65];[30];[20,30];;v1;;{'operational_temperature':'akbar_review_2020','investment_cost':'sterner_power--gas_2021','fixed_cost':'rego_de_vasconcelos_recent_2019','electricity_demand':'rego_de_vasconcelos_recent_2019','process_efficiency':'akbar_review_2020','operational_lifetime':'gotz_renewable_2016','minimal_load':'akbar_review_2020'};"

    assert upload.fix_json_encoding(valid_json) == valid_json
    assert upload.fix_json_encoding(invalid_json) == valid_json

def test_resources_with_valid_json():
    filename = TEST_DATA_FOLDER / "valid_json.csv"
    with filename.open("rb") as csvfile:
        data = {"table": csvfile.read()}
    resources = upload.get_resources_from_data(data, {"table": METADATA})
    assert len(resources) == 1
    report = resources[0].validate()
    assert report.valid is True
    df = resources[0].to_pandas()
    source = df["source"].iloc[0]
    assert isinstance(source, dict) is True
    assert len(source) == 7

def test_resources_with_invalid_json():
    filename = TEST_DATA_FOLDER / "invalid_json.csv"
    with filename.open("rb") as csvfile:
        data = {"table": csvfile.read()}
    resources = upload.get_resources_from_data(data, {"table": METADATA})
    assert len(resources) == 1
    report = resources[0].validate()
    assert report.valid is True
    df = resources[0].to_pandas()
    source = df["source"].iloc[0]
    assert isinstance(source, dict) is True
    assert len(source) == 7