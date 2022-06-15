from oedatamodel_api import settings

settings.MAPPINGS_DIR = settings.ROOT_DIR / "tests" / "mappings"

from oedatamodel_api import mapping_custom  # noqa: E402


def test_mapping_chain():
    data = {"a": {"b": 1, "c": 2}, "b": {"b": 5, "c": 33}}
    mapped_data = mapping_custom.apply_custom_mapping(
        data, project=None, mapping="chain"
    )
    assert mapped_data == {"result": 1}


def test_old_mapping_chain():
    data = {"a": {"b": 1, "c": 2}, "b": {"b": 5, "c": 33}}
    mapped_data = mapping_custom.apply_custom_mapping(data, project=None, mapping="old")
    assert mapped_data == {"result": 1}


def test_project_mapping():
    data = {"a": {"b": 1, "c": 2}, "b": {"b": 5, "c": 33}}
    mapped_data = mapping_custom.apply_custom_mapping(
        data, project="subproject", mapping="chain"
    )
    assert mapped_data == {"result": 5}
