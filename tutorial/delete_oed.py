from oem2orm import oep_oedialect_oem2orm as oem2orm
import os
import getpass


if __name__ == "__main__":
    oem2orm.setup_logger()
    os.environ["OEP_TOKEN"] = getpass.getpass('Token:')
    db = oem2orm.setup_db_connection()
    metadata_folder = oem2orm.select_oem_dir(oem_folder_name="metadata")
    tables_orm = oem2orm.collect_tables_from_oem(db, metadata_folder)

    oem2orm.create_tables(db, tables_orm)
    oem2orm.delete_tables(db, tables_orm)