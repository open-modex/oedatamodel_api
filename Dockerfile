FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7

ENV HOST 0.0.0.0
ENV PORT 5001
ENV DEBUG true

WORKDIR /tmp

# install requirements
COPY ./pyproject.toml ./poetry.lock ./
RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-dev --no-root

COPY . /fastapi_app
WORKDIR /fastapi_app

# expose the app port
EXPOSE 5001

# run the app server, the last argument match the app variable in the webapp.py file
CMD ["uvicorn", "oedatamodel_api.webapp:app", "--host", "0.0.0.0", "--port", "5001"]