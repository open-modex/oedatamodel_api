import os
import pathlib
from dotenv import load_dotenv
import requests

load_dotenv()

path = pathlib.Path("Path to CSVs")

CSVS = list(path.iterdir())

account = os.getenv("account")
api_key = os.getenv("api_key")
group = os.getenv("group")
version = os.getenv("version")
databus_url = os.getenv("databus_url")

for file in CSVS:
    response = requests.post(
        databus_url,
        data={
            "schema": "model_draft",
            "account": account,
            "api_key": api_key,
            "group": group,
            "table": pathlib.Path(file).name.split(".")[0],
            "version": version,
        },
    )
    print(response)
