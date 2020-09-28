# API to connect OEP with MODEX frameworks

This API works as a connector between the OEP and energy system modelling frameworks from MODEX project.
Scenario data stored in the OEP can be requested by the API and will be parsed and provided for requesting framework.

## Get started

Run `sudo docker-compose up -d --build` to run the task queue and the webapp simulaneously.

Now the webapp is available at `127.0.0.1:5001`

Run `sudo docker-compose down` to shut the services down.

## Develop while services are running

### Using [fastapi](https://fastapi.tiangolo.com/)

In another terminal go the the root of the repo and run `. fastapi_run.sh`

Now the fast app is available at `127.0.0.1:5001`

While docker runs :
https://vsupalov.com/rebuilding-docker-image-development/

## Docs

To build the docs simply go to the `docs` folder

    cd docs

Install the requirements

    pip install -r docs_requirements.txt

and run

    make html

The output will then be located in `docs/_build/html` and can be opened with your favorite browser

## Code linting

TODO

