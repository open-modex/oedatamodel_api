import os
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


app = FastAPI()

SERVER_ROOT = os.path.dirname(__file__)

app.mount(
    "/static", StaticFiles(directory=os.path.join(SERVER_ROOT, "static")), name="static"
)

templates = Jinja2Templates(directory=os.path.join(SERVER_ROOT, "templates"))


@app.get("/")
def index(request: Request) -> Response:
    return templates.TemplateResponse("index.html", {"request": request})
