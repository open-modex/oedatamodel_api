
import os
import pathlib
import warnings

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
APP_DIR = ROOT_DIR / "oedatamodel_api"
APP_STATIC_DIR = ROOT_DIR / "oedatamodel_api" / 'static'
SOURCES_DIR = APP_DIR / "sources"
MAPPINGS_DIR = APP_DIR / "mappings"
UPLOAD_DIR = ROOT_DIR / "upload_data"
ZIP_UPLOAD_FILEPATH = ROOT_DIR / "files" / "datapackage.zip"

# OEP
# ---
OEP_URL = "https://openenergy-platform.org"
OEP_TOKEN = os.environ.get("OEP_TOKEN")
if OEP_TOKEN is None:
    warnings.warn("No OEP token given - some functionality may not work")

# OEDATAMODEL
# -----------
OEDATAMODEL_META_DIR = APP_DIR / "datamodel"
OEDATAMODEL_SCHEMA = "model_draft"
NORMALIZED_TABLES = ("oed_scenario", "oed_data", "oed_scalar", "oed_timeseries")
CONCRETE_TABLES = ("oed_scenario", "oed_scalar", "oed_timeseries")
