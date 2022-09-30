import json
import logging
import os
import tempfile
import warnings
from typing import List, Union

import frictionless
import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from oedatamodel_api import formatting, mapping_custom
from oedatamodel_api import metadata as oem
from oedatamodel_api import upload
from oedatamodel_api.oep_connector import (
    OEPDataNotFoundError,
    SourceNotFound,
    get_data_from_oep,
)
from oedatamodel_api.package_docs import loadFromJsonFile
from oedatamodel_api.settings import APP_STATIC_DIR, ROOT_DIR, UPLOAD_FILEPATH, VERSION
from oedatamodel_api.validation import (
    DatapackageNotValid,
    create_and_validate_datapackage,
)

app = FastAPI()
app.mount(
    "/static",
    StaticFiles(directory=ROOT_DIR / "oedatamodel_api" / "static"),
    name="static",
)
templates = Jinja2Templates(directory=ROOT_DIR / "oedatamodel_api" / "templates")

logger = logging.getLogger("uvicorn.error")


@app.get("/")
def index(request: Request) -> Response:
    try:
        docs_coustom_mapping = loadFromJsonFile(
            APP_STATIC_DIR, "docs_custom_mapping.json"
        )
        docs_current_mappings = loadFromJsonFile(
            APP_STATIC_DIR, "docs_current_mappings.json"
        )
    except FileNotFoundError:
        docs_coustom_mapping = [{}]
        docs_current_mappings = [{}]

    return templates.TemplateResponse(
        "index.html",
        {
            "version": VERSION,
            "request": request,
            "module_docs": docs_coustom_mapping,
            "mappings_docs": docs_current_mappings,
        },
    )


def prepare_response(raw_json, project, mapping, output_format):
    try:
        mapped_data = mapping_custom.apply_custom_mapping(raw_json, project, mapping)
    except Exception as e:
        return HTMLResponse(str(e))

    try:
        response = formatting.format_data(mapped_data, output_format)
    except TypeError as te:
        return HTMLResponse(
            f'Error while creating zip file from result json:<br>{"<br>".join(te.args)}'
            "<br>Maybe mapping is not supported for chosen output format?",
        )
    return response


@app.get("/query")
def query(
    source: str,
    mapping: str,
    request: Request,
    project: Union[str, None] = None,
    output: formatting.OutputFormat = formatting.OutputFormat.json,
):
    query_params = {
        k: v
        for k, v in request.query_params.items()
        if k not in ("source", "mapping", "project", "output")
    }
    try:
        raw_data = get_data_from_oep(project, source, **query_params)
    except (ConnectionError, OEPDataNotFoundError, SourceNotFound) as e:
        return {"error": e.args}
    return prepare_response(raw_data, project, mapping, output)


@app.get("/scenario/id/{scenario_id}")
def scenario_by_id(
    scenario_id: int,
    source: str,
    mapping: str,
    project: Union[str, None] = None,
    output: formatting.OutputFormat = formatting.OutputFormat.json,
):
    try:
        raw_data = get_data_from_oep(project, source, scenario_id=scenario_id)
    except (ConnectionError, OEPDataNotFoundError) as e:
        return {"error": e.args}
    return prepare_response(raw_data, project, mapping, output)


@app.get("/scenario/name/{scenario_name}")
def scenario_by_name(
    scenario_name: str,
    source: str,
    mapping: str,
    project: Union[str, None] = None,
    output: formatting.OutputFormat = formatting.OutputFormat.json,
):
    try:
        raw_data = get_data_from_oep(project, source, scenario_name=scenario_name)
    except (ConnectionError, OEPDataNotFoundError) as e:
        return {"error": e.args}
    return prepare_response(raw_data, project, mapping, output)


@app.get("/upload_datapackage/")
async def upload_datapackage_view():
    content = """
<body>
<form action="/upload_datapackage/" enctype="multipart/form-data" method="post">
    <p>
        <label for="token">OEP Token</label>
        <input name="token" type="text">
    </p>
    <p>
        <label for="datapackage_files">Upload datapackage files (must include "datapackage.json")</label>
        <input name="datapackage_files" type="file" multiple>
    </p>
    <p>
        <label for="schema">Schema</label>
        <input name="schema" type="text" value="model_draft">
    </p>
    <p>
        <label for="mapping">Mapping (optional)</label>
        <input name="mapping" type="text">
    </p>
    <p>
        <label for="show_json">Show data after mapping (instead of upload)</label>
        <input name="show_json" type="checkbox" id="show_json">
    </p>
    <p>
        <label for="adapt_foreign_keys">Adapt foreign keys (foreign keys are automatically set)</label>
        <input name="adapt_foreign_keys" type="checkbox" id="adapt_foreign_keys">
    </p>
    <p><input type="submit"></p>
</form>
</body>
    """
    logger.debug("Validating datapackage...")
    return HTMLResponse(content=content)


def get_datapackage(datapackage_path):
    logger.debug("Validating datapackage...")
    try:
        package = create_and_validate_datapackage(datapackage_path)
    except DatapackageNotValid as de:
        raise HTTPException(
            status_code=404, detail={"Datapackage is not valid": de.args[0]}
        ) from de
    return package


def apply_mapping(data_json, project, mapping):
    if not mapping:
        return data_json
    try:
        mapped_json = mapping_custom.apply_custom_mapping(data_json, project, mapping)
        logger.debug("Successfully applied mapping")
        return mapped_json
    except Exception as e:
        raise HTTPException(status_code=404, detail={"Mapping error": str(e)}) from e


def validate_upload(data_json, schema):
    # Validate extracted (mapped) data against OEP table formats
    upload_warnings = []
    with warnings.catch_warnings(record=True) as w:
        try:
            upload.validate_upload_data(data_json, schema)
        except (upload.ValidationError, upload.UploadError) as e:
            raise HTTPException(
                status_code=404, detail={"OEP data validation error": e.args[0]}
            ) from e

        upload_warnings.extend(w)
    logger.debug("Successfully validated upload data with OEP metadata")
    return upload_warnings


@app.post("/upload_datapackage/")
async def upload_datapackage(
    datapackage_files: List[UploadFile] = None,
    schema: str = Form(default=""),
    mapping: str = Form(default=""),
    project: Union[str, None] = Form(default=None),
    show_json: bool = Form(default=False),
    adapt_foreign_keys: bool = Form(default=False),
    token: str = Form(default=None),
):
    if not token:
        return HTMLResponse("Invalid token - you must provide a valid OEP Token")

    # Create temporary directory to store datapackage:
    with tempfile.TemporaryDirectory(dir=UPLOAD_FILEPATH) as tempdir:
        for upload_file in datapackage_files:
            with open(
                os.path.join(tempdir, upload_file.filename), "wb+"
            ) as file_object:
                file_object.write(upload_file.file.read())
        logger.debug("Successfully extracted datapackage to temp folder")

        package = get_datapackage(f"{tempdir}/datapackage.json")
        data_json = {
            resource.name: [row.to_dict() for row in resource.read_rows()]
            for resource in package.resources
        }

    mapped_json = apply_mapping(data_json, project, mapping)

    # Return mapped data (optional)
    if show_json:
        return mapped_json

    upload_warnings = validate_upload(data_json, schema)
    # Prepare success response
    success_response = {
        "success": "Upload of datapackage successful!",
        "warnings": [str(warning.message) for warning in upload_warnings],
    }

    # Adapt foreign keys (Modex-specific)
    if adapt_foreign_keys:
        try:
            data_json, scenario_id = upload.adapt_foreign_keys(data_json, schema)
        except upload.UploadError as ue:
            raise HTTPException(
                status_code=404, detail={"error on upload": str(ue)}
            ) from ue
        success_response["scenario_id"] = scenario_id
        logger.debug("Successfully adapted foreign keys")

    # Finally, upload data to OEP
    try:
        upload.upload_data_to_oep(data_json, schema, token)
    except upload.UploadError as ue:
        raise HTTPException(
            status_code=404, detail={"error on upload": str(ue)}
        ) from ue

    logger.info(f"Successfully uploaded datapackage '{package.name}' to OEP")

    return success_response


@app.get("/upload/")
async def upload_single_table_view(request: Request):
    return templates.TemplateResponse(
        "single_upload.html", context={"request": request}
    )


@app.post("/upload/")
async def upload_single_table(
    csv_file: UploadFile = File(...),
    schema: str = Form(default=None),
    table: str = Form(default=None),
    token: str = Form(default=None),
):
    if not token:
        raise HTTPException(
            status_code=404, detail="Invalid token - you must provide a valid OEP Token"
        )
    resource = frictionless.Resource(csv_file.file.read())
    data = {table: [row.to_dict() for row in resource.read_rows()]}

    validate_upload(data, schema)
    try:
        upload.upload_data_to_oep(data, schema, token)
    except upload.UploadError as ue:
        raise HTTPException(
            status_code=404, detail={"error on upload": str(ue)}
        ) from ue

    success_msg = "Successfully uploaded data from CSV to OEP"
    logger.info(success_msg)
    return success_msg


@app.get("/create_table/")
async def create_table_view(request: Request):
    return templates.TemplateResponse("metadata.html", context={"request": request})


@app.post("/create_table/")
async def create_table(
    metadata_file: UploadFile = File(...),
    user: str = Form(default=None),
    token: str = Form(default=None),
):
    if not token:
        raise HTTPException(
            status_code=404, detail="Invalid token - you must provide a valid OEP Token"
        )
    metadata = json.load(metadata_file.file)
    try:
        oem.check_parameter_model(metadata)
    except oem.ParameterModelException as pme:
        raise HTTPException(
            status_code=404,
            detail={"Error while creating OEP tables from OEM": str(pme)},
        ) from pme
    oem.create_tables_from_metadata(metadata, user, token)
    schema, tablename = metadata["resources"][0]["name"].split(".")
    table_url = f"https://openenergy-platform.org/dataedit/view/{schema}/{tablename}"
    return f"Successfully created table '{schema}.{tablename}' on OEP. Table should now be available under: {table_url}"


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")  # noqa: S104
