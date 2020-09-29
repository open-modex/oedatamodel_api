import os
import uvicorn

from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from oedatamodel_api.oep_connector import get_scenario_response_from_oep, get_scenario_data

app = FastAPI()

SERVER_ROOT = os.path.dirname(__file__)

app.mount(
    '/static', StaticFiles(directory=os.path.join(SERVER_ROOT, 'static')), name='static',
)
templates = Jinja2Templates(directory=os.path.join(SERVER_ROOT, 'templates'))


@app.get('/')
def index(request: Request) -> Response:
    return templates.TemplateResponse('index.html', {'request': request})


@app.get('/scenario/id/{scenario_id}')
def scenario_by_id(scenario_id: int):
    scenario_json = get_scenario_response_from_oep(scenario_id=scenario_id)
    return get_scenario_data(scenario_json)


@app.get('/scenario/name/{scenario_name}')
def scenario_by_name(scenario_name: str):
    scenario_json = get_scenario_response_from_oep(scenario_name=scenario_name)
    return get_scenario_data(scenario_json)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
