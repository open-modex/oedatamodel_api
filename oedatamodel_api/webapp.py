
import uvicorn

from fastapi import FastAPI, Request, Response, UploadFile, File
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from oedatamodel_api.oep_connector import get_data_from_oep, OEPDataNotFoundError
from oedatamodel_api import mapping_custom, formatting, upload
from oedatamodel_api.settings import ROOT_DIR

app = FastAPI()

app.mount(
    '/static', StaticFiles(directory=ROOT_DIR / "oedatamodel_api" / 'static'), name='static',
)
templates = Jinja2Templates(directory=ROOT_DIR / "oedatamodel_api" / 'templates')


@app.get('/')
def index(request: Request) -> Response:
    return templates.TemplateResponse('index.html', {'request': request})


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
async def main():
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
async def create_upload_file(zip_file: UploadFile = File(...)):
    try:
        scenario_id = upload.upload_csv_from_zip(zip_file)
    except Exception as e:
        return {"error": str(e)}
    return {
        "success": f"Upload of file '{zip_file.filename}' successful!",
        "scenario_id": scenario_id
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
