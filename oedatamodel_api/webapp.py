
import uvicorn
import pandas

from fastapi import FastAPI, Request, Response, UploadFile, File, Form
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from oedatamodel_api.oep_connector import get_data_from_oep, OEPDataNotFoundError
from oedatamodel_api import mapping_custom, formatting, upload
from oedatamodel_api.settings import ROOT_DIR, APP_STATIC_DIR

from oedatamodel_api.package_docs import loadFromJsonFile

app = FastAPI()

app.mount(
    '/static', StaticFiles(directory=ROOT_DIR / "oedatamodel_api" / 'static'), name='static',
)
templates = Jinja2Templates(directory=ROOT_DIR / "oedatamodel_api" / 'templates')


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

    if output_format == formatting.OutputFormat.csv:
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
    else:
        return mapped_data


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


@app.get("/upload_csv/")
async def upload_csv_file_view():
    content = """
<body>
<form action="/upload_csv/" enctype="multipart/form-data" method="post">
<input name="zip_file" type="file">
<input type="submit">
</form>
</body>
    """
    return HTMLResponse(content=content)


@app.post("/upload_csv/")
async def upload_csv_file(zip_file: UploadFile = File(...)):
    try:
        scenario_id = upload.upload_csv_from_zip(zip_file)
    except Exception as e:
        return {"error": str(e)}
    return {
        "success": f"Upload of file '{zip_file.filename}' successful!",
        "scenario_id": scenario_id
    }


@app.get("/upload_csv_mapping/")
async def upload_csv_file_via_mapping_view():
    content = """
<body>
<form action="/upload_csv_mapping/" enctype="multipart/form-data" method="post">
<input name="zip_file" type="file">
<input name="mapping" type="text">
<input name="show_json" type="checkbox" id="show_json" checked>
<label for="show_json">Show JSON</label>
<input type="submit">
</form>
</body>
    """
    return HTMLResponse(content=content)


@app.post("/upload_csv_mapping/")
async def upload_csv_file_via_mapping(
        zip_file: UploadFile = File(...),
        mapping: str = Form(...),
        show_json: bool = Form(False)
):
    try:
        mapped_json = upload.get_mapped_json_from_zip(zip_file, mapping)
    except Exception as e:
        return {"error in mapping": str(e)}
    if show_json:
        return mapped_json

    dfs = upload.create_dfs_from_json(mapped_json)
    try:
        scenario_id = upload.upload_dfs(dfs)
    except Exception as e:
        return {"error on upload": str(e)}
    return {
        "success": f"Upload of file '{zip_file.filename}' successful!",
        "scenario_id": scenario_id
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
