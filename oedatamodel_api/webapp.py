import os
import uvicorn

from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from oedatamodel_api.oep_connector import get_scenario_from_oep, ScenarioNotFoundError
from oedatamodel_api import mapping_custom, formatting

app = FastAPI()

SERVER_ROOT = os.path.dirname(__file__)

app.mount(
    '/static', StaticFiles(directory=os.path.join(SERVER_ROOT, 'static')), name='static',
)
templates = Jinja2Templates(directory=os.path.join(SERVER_ROOT, 'templates'))


@app.get('/')
def index(request: Request) -> Response:
    return templates.TemplateResponse('index.html', {'request': request})


def prepare_response(raw_json, mapping, output_format):
    try:
        mapped_data = mapping_custom.apply_custom_mapping(raw_json, mapping)
    except mapping_custom.MappingNotFound as me:
        return HTMLResponse('<br>'.join(me.args))

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
    mapping: str,
    output: formatting.OutputFormat = formatting.OutputFormat.json
):
    try:
        raw_scenario_json = get_scenario_from_oep(scenario_id=scenario_id)
    except (ConnectionError, ScenarioNotFoundError) as e:
        return {"error": e.args}
    return prepare_response(raw_scenario_json, mapping, output)


@app.get('/scenario/name/{scenario_name}')
def scenario_by_name(
    scenario_name: str,
    mapping: str,
    output: formatting.OutputFormat = formatting.OutputFormat.json
):
    try:
        raw_scenario_json = get_scenario_from_oep(scenario_name=scenario_name)
    except (ConnectionError, ScenarioNotFoundError) as e:
        return {"error": e.args}
    return prepare_response(raw_scenario_json, mapping, output)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
