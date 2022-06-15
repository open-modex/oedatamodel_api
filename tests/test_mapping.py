from oedatamodel_api import settings

settings.MAPPINGS_DIR = settings.ROOT_DIR / "tests" / "mappings"

from oedatamodel_api import mapping_custom  # noqa: E402


def test_mapping_chain():
    data = {"a": {"b": 1, "c": 2}}
    mapped_data = mapping_custom.apply_custom_mapping(data, "chain")
    assert mapped_data == {"result": 1}


def test_old_mapping_chain():
    data = {"a": {"b": 1, "c": 2}}
    mapped_data = mapping_custom.apply_custom_mapping(data, "old")
    assert mapped_data == {"result": 1}
