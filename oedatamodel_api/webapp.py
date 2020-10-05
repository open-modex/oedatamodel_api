import os
import uvicorn

from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from oedatamodel_api.oep_connector import get_scenario_from_oep, ScenarioNotFoundError
from oedatamodel_api import transform

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
    mapped_data = transform.map_data(raw_json, mapping)

    if output_format == transform.OutputFormat.csv:
        zipped_data = transform.create_zip_csv(mapped_data)
        response = StreamingResponse(zipped_data, media_type="application/x-zip-compressed")
        response.headers["Content-Disposition"] = f"attachment; filename=scenario.zip"
        return response
    else:
        return mapped_data


@app.get('/scenario/id/{scenario_id}')
def scenario_by_id(
    scenario_id: int,
    mapping: transform.OedataMapping = transform.OedataMapping.raw,
    output: transform.OutputFormat = transform.OutputFormat.json
):
    try:
        raw_scenario_json = get_scenario_from_oep(scenario_id=scenario_id)
    except (ConnectionError, ScenarioNotFoundError) as e:
        return {"error": e.args}
    return prepare_response(raw_scenario_json, mapping, output)


@app.get('/scenario/name/{scenario_name}')
def scenario_by_name(
    scenario_name: str,
    mapping: transform.OedataMapping = transform.OedataMapping.raw,
    output: transform.OutputFormat = transform.OutputFormat.json
):
    try:
        raw_scenario_json = get_scenario_from_oep(scenario_name=scenario_name)
    except (ConnectionError, ScenarioNotFoundError) as e:
        return {"error": e.args}
    return prepare_response(raw_scenario_json, mapping, output)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
