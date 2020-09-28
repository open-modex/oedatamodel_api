#!bin/bash
# From the root of the repository, type `python flask_run.py` to start the flask server
uvicorn oedatamodel_api.webapp:app --reload --port 5001