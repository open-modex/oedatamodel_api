import os
import pathlib

VERSION = "0.11.0"
DEBUG = os.environ.get("DEBUG", "False") == "True"

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
APP_DIR = ROOT_DIR / "oedatamodel_api"
APP_STATIC_DIR = ROOT_DIR / "oedatamodel_api" / "static"
SOURCES_DIR = APP_DIR / "sources"
MAPPINGS_DIR = APP_DIR / "mappings"
UPLOAD_DIR = ROOT_DIR / "upload_data"
UPLOAD_FILEPATH = ROOT_DIR / "files"

# OEP
# ---
OEP_URL = "https://openenergy-platform.org"
DATABUS_URI_BASE = "https://energy.databus.dbpedia.org"
MOSS_URL = "http://moss.tools.dbpedia.org/annotation-api-demo/submit"
OEDATAMODEL_API = "https://modex.rl-institut.de/"  # Only used in debug mode


# REDIS CACHE
# -----------
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")


# OEDATAMODEL
# -----------
OEDATAMODEL_META_DIR = APP_DIR / "datamodel"
OEDATAMODEL_SCHEMA = "model_draft"
NORMALIZED_TABLES = ("oed_scenario", "oed_data", "oed_scalar", "oed_timeseries")
CONCRETE_TABLES = ("oed_scenario", "oed_scalar", "oed_timeseries")
