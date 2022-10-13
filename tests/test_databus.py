from pytest import raises
from oedatamodel_api import databus


def test_metadata_check_missing_tables():
    with raises(databus.MetadataError):
        databus.get_table_meta("missing_schema", "missing_table")

    with raises(databus.MetadataError) as e:
        databus.get_table_meta("model_draft", "missing_table")


def test_metadata_check_emptiness():
    with raises(databus.MetadataError) as e:
        databus.get_table_meta("model_draft", "CountryValues1")
    assert "empty" in str(e)


def test_metadata_abstract_and_license():
    metadata = databus.get_table_meta("model_draft", "oed_scenario")
    abstract = metadata["context"]["documentation"]
    assert (
        abstract
        == "https://github.com/OpenEnergyPlatform/oedatamodel/blob/develop/README.md"
    )
    license_ = metadata["licenses"][0]["path"]
    assert license_ == "https://creativecommons.org/licenses/by/4.0/legalcode"
