import os
import pathlib

import requests

from dotenv import load_dotenv

load_dotenv()

path = pathlib.Path("Path to csvs")

CSVS = list(path.iterdir())

TOKEN = os.getenv("TOKEN")
upload_csv_url = os.getenv("upload_csv_url")

for file in CSVS:
    response = requests.post(
        upload_csv_url,
        data={
            "schema": "model_draft",
            "token": TOKEN,
            "table": pathlib.Path(file).name.split(".")[0],
        },
        files=[("csv_file", (pathlib.Path(file).name, open(file, "rb")))],
    )
    print(response)
