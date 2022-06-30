from oedatamodel_api import settings

settings.SOURCES_DIR = settings.ROOT_DIR / "tests" / "sources"

from oedatamodel_api import oep_connector  # noqa: E402


def test_simple_source():
    data = oep_connector.get_data_from_oep(project=None, source="simple_source")
    assert "content" in data


def test_multiple_source():
    data = oep_connector.get_data_from_oep(project=None, source="multiple_sources")
    assert "scenario" in data
    assert "content" in data["scenario"]
    assert "scenario2" in data
    assert "content" in data["scenario2"]
