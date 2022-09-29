import logging

import sqlalchemy as sa
from oem2orm.oep_oedialect_oem2orm import (
    DB,
    create_tables,
    create_tables_from_metadata_file,
)

logger = logging.getLogger("uvicorn.access")

OEP_CONNECTION = "postgresql+oedialect://{user}:{token}@openenergy-platform.org"


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
    create_tables(db, tables)
    logging.info("Successfully created tables from OEM on OEP.")
