
import uvicorn
import warnings
import logging
from typing import List

from fastapi import FastAPI, Request, Response, UploadFile, File, Form
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from oedatamodel_api.oep_connector import get_data_from_oep, OEPDataNotFoundError
from oedatamodel_api import mapping_custom, formatting, upload
from oedatamodel_api.settings import ROOT_DIR, APP_STATIC_DIR
from oedatamodel_api.package_docs import loadFromJsonFile
from oedatamodel_api.validation import create_and_validate_datapackage, DatapackageNotValid

app = FastAPI()
app.mount(
    '/static', StaticFiles(directory=ROOT_DIR / "oedatamodel_api" / 'static'), name='static',
)
templates = Jinja2Templates(directory=ROOT_DIR / "oedatamodel_api" / 'templates')

logger = logging.getLogger("uvicorn.error")


@app.get('/')
def index(request: Request) -> Response:
    try:
        docs_coustom_mapping = loadFromJsonFile(APP_STATIC_DIR, "docs_custom_mapping.json")
        docs_current_mappings = loadFromJsonFile(APP_STATIC_DIR, "docs_current_mappings.json")
    except:
        docs_coustom_mapping = [{}]
        docs_current_mappings = [{}]

    return templates.TemplateResponse('index.html', {'request': request,
                                                     "module_docs": docs_coustom_mapping,
                                                     "mappings_docs": docs_current_mappings})


def prepare_response(raw_json, mapping, output_format):
    try:
        mapped_data = mapping_custom.apply_custom_mapping(raw_json, mapping)
    except Exception as e:
        return HTMLResponse(str(e))

    if output_format != formatting.OutputFormat.csv:
        return mapped_data
    try:
        zipped_data = formatting.create_zip_csv(mapped_data)
    except TypeError as te:
        return HTMLResponse(
            'Error while creating zip file from result json:<br>"' +
            '<br>'.join(te.args) +
            '"<br>Maybe mapping is not supported for chosen output format?'
        )
    response = StreamingResponse(zipped_data, media_type="application/x-zip-compressed")
    response.headers["Content-Disposition"] = f"attachment; filename=scenario.zip"
    return response


@app.get('/scenario/id/{scenario_id}')
def scenario_by_id(
    scenario_id: int,
    source: str,
    mapping: str,
    output: formatting.OutputFormat = formatting.OutputFormat.json
):
    try:
        raw_data = get_data_from_oep(source, scenario_id=scenario_id)
    except (ConnectionError, OEPDataNotFoundError) as e:
        return {"error": e.args}
    return prepare_response(raw_data, mapping, output)


@app.get('/scenario/name/{scenario_name}')
def scenario_by_name(
    scenario_name: str,
    source: str,
    mapping: str,
    output: formatting.OutputFormat = formatting.OutputFormat.json
):
    try:
        raw_data = get_data_from_oep(source, scenario_name=scenario_name)
    except (ConnectionError, OEPDataNotFoundError) as e:
        return {"error": e.args}
    return prepare_response(raw_data, mapping, output)


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


@app.post("/upload_datapackage/")
async def upload_datapackage(
        datapackage_files: List[UploadFile] = None,
        schema: str = Form(...),
        mapping: str = Form(None),
        show_json: bool = Form(False),
        adapt_foreign_keys: bool = Form(False),
        token: str = Form(None)
):
    if not token:
        return HTMLResponse("Invalid token - you must provide a valid OEP Token")

    # Validate and extract data from uploaded datapackage
    logger.debug("Validating datapackage...")
    try:
        package = create_and_validate_datapackage(datapackage_files)
    except DatapackageNotValid as de:
        return {"Datapackage is not valid": de.args[0]}
    logger.info(f"Successfully validated datapackage '{package.name}'")
    data_json = {resource.name: [row.to_dict() for row in resource.read_rows()] for resource in package.resources}

    # Apply mappings (optional)
    if mapping:
        try:
            data_json = mapping_custom.apply_custom_mapping(data_json, mapping)
        except Exception as e:
            return {"Mapping error": str(e)}
        logger.debug(f"Successfully applied mapping")

    # Return mapped data (optional)
    if show_json:
        return data_json

    # Validate extracted (mapped) data against OEP table formats
    upload_warnings = []
    with warnings.catch_warnings(record=True) as w:
        try:
            upload.validate_upload_data(data_json, schema)
        except upload.ValidationError as ve:
            return {"OEP data validation error": ve.args[0]}
        upload_warnings.extend(w)
    logger.debug(f"Successfully validated upload data with OEP metadata")

    # Prepare success response
    success_response = {
        "success": f"Upload of file '{zipped_datapackage.filename}' successful!",
        "warnings": [str(warning.message) for warning in upload_warnings]
    }

    # Adapt foreign keys (Modex-specific)
    if adapt_foreign_keys:
        data_json, scenario_id = upload.adapt_foreign_keys(data_json, schema)
        success_response["scenario_id"] = scenario_id
        logger.debug(f"Successfully adapted foreign keys")

    # Finally, upload data to OEP
    try:
        upload.upload_data_to_oep(data_json, schema, token)
    except upload.UploadError as ue:
        return {"error on upload": str(ue)}
    logger.info(f"Successfully uploaded datapackage '{package.name}' to OEP")

    return success_response


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")
