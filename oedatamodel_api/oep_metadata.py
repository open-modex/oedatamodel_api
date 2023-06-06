import logging

import sqlalchemy as sa
from oem2orm.oep_oedialect_oem2orm import (
    DB,
    DatabaseError,
    MetadataError,
    api_updateMdOnTable,
    create_tables,
    create_tables_from_metadata_file,
)

logger = logging.getLogger("uvicorn.access")

OEP_CONNECTION = "postgresql+oedialect://{user}:{token}@openenergy-platform.org"

DEFAULT_FRICTIONLESS_RESOURCE = {
    "profile": "tabular-data-resource",
    "scheme": "file",
    "format": "csv",
    "encoding": "utf-8",
    "schema": {
        "fields": [],
    },
    "dialect": {"delimiter": ";"},
}

FRICTIONLESS_TYPES = {
    "bigint": "integer",
    "float": "number",
    "json": "object",
    "text": "string",
}
DEFAULT_FRICTIONLESS_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class ParameterModelException(Exception):
    """Raised if OEM is invalid with parameter model schema"""


def create_db_connection(user: str, token: str):
    conn_str = OEP_CONNECTION.format(user=user, token=token)
    engine = sa.create_engine(conn_str)
    metadata = sa.MetaData(bind=engine)
    return DB(engine, metadata)


def check_parameter_model(metadata):
    if len(metadata["resources"]) > 1:
        raise ParameterModelException(
            "More than one table defined in metadata resources. "
            "Parameter model consists of a single table."
        )
    logging.info("Successfully checked OEM parameter model schema.")


def create_tables_from_metadata(metadata: dict, user: str, token: str):
    db = create_db_connection(user, token)
    tables = create_tables_from_metadata_file(db, metadata)
    try:
        create_tables(db, tables)
    except DatabaseError as de:
        raise ParameterModelException(str(de))
    if len(tables) == 1:
        # Check if schema is set:
        if len(metadata["resources"][0]["name"].split(".")) != 2:
            raise ParameterModelException(
                "Resource name must include OEP schema, "
                "otherwise metadata upload fails. (Example: 'model_draft.tablename')."
            )
        # Upload metadata for single table
        try:
            api_updateMdOnTable(metadata, token)
        except MetadataError as me:
            raise ParameterModelException(
                f"Following error occurs when trying to upload metadata: {str(me)}"
            )
    logging.info("Successfully created tables from OEM on OEP.")
